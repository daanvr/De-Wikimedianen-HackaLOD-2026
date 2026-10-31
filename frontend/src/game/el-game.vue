<script setup>
    // The game: sail the Siboga yourself, stoke the boiler, discover the sea and collect real
    // specimens that float at made-up places. Separate from the explore mode; see docs/spelmodus.md.
    // This component runs the game loop and ties the map, the controls and the overlays together.
    import { computed, inject, onBeforeUnmount, onMounted, ref, shallowRef, toRaw } from 'vue';
    import { pointAt } from '@/explorer/data.js';
    import { ICON_PATHS, groupIcon, groupName } from '@/explorer/groups.js';
    import { newAchievements } from './achievements.js';
    import { createCrew } from './crew.js';
    import { loadGame } from './data.js';
    import { createFog } from './fog.js';
    import { bearingTo, distanceKm, moveKm } from './geo.js';
    import { createLandMask, createWaterGrid } from './land.js';
    import { createMission } from './missions.js';
    import { PRESSURE_FLOOR, createShip, shovel, step } from './physics.js';
    import { RARITIES, assignRarities, pointsOf } from './rarity.js';
    import { clearProgress, loadMuted, loadProgress, saveMuted, saveProgress } from './save.js';
    import { createSound } from './sound.js';
    import { placeSpecimens } from './spawn.js';
    import { ACHIEVEMENTS } from './texts.js';
    import ElGameAlbum from './el-game-album.vue';
    import ElGameBoiler from './el-game-boiler.vue';
    import ElGameEquator from './el-game-equator.vue';
    import ElGameHelm from './el-game-helm.vue';
    import ElGameHud from './el-game-hud.vue';
    import ElGameIntro from './el-game-intro.vue';
    import ElGameMap from './el-game-map.vue';

    // Specimens within this distance of the ship are drawn and float about
    const NEAR_KM = 250;
    // They drift towards a ship this close, and are caught closer than this
    const MAGNET_KM = 13;
    const STATION_MAGNET_KM = 35;
    const CATCH_KM = 5;
    const DRIFT_KM = 1.6;
    const STATION_KM = 14;
    const OFF_COURSE_KM = 120;
    const QUIET_SECONDS = 20;
    const IDLE_SECONDS = 30;
    const SAVE_SECONDS = 5;
    const MILESTONES = [25, 100, 250, 500, 1000, 2500];
    const ALGAE = new Set(['Roodwieren', 'Bruinwieren', 'Groenwieren', 'Blauwalgen']);
    const TOAST_SECONDS = {
        crew : 7,
        specimen : 4.5,
        achievement : 5,
        note : 4
    };
    const MAX_TOASTS = 3;
    const RARE_TOAST_SECONDS = 8;
    const START_CLEARANCE_KM = 8;
    const MISSION_GIVE_UP_KM = 1200;
    const ICON_KEYS = new Map(Object.entries(ICON_PATHS).map(([key, path]) => [path, key]));

    const store = inject('store');

    const phase = ref('loading');
    const loadingText = ref('Kaart tekenen…');
    const hasSave = ref(false);
    const start = shallowRef(null);
    const fogCanvas = shallowRef(null);
    const map = ref(null);
    const hud = ref(null);
    const pressure = ref(PRESSURE_FLOOR);
    const isVenting = ref(false);
    const score = ref(0);
    const collectedCount = ref(0);
    const discovered = ref(0);
    const missionView = ref(null);
    const compass = ref(null);
    const toasts = ref([]);
    const isMuted = ref(loadMuted());
    const isInfoOpen = ref(false);
    const album = shallowRef(null);
    const equator = shallowRef(null);
    const total = ref(0);
    const gameStations = shallowRef([]);
    const gameLine = shallowRef([]);

    const isPaused = computed(() => phase.value !== 'playing' || isInfoOpen.value || Boolean(album.value) || Boolean(equator.value));

    let data = null;
    let land = null;
    let grid = null;
    let fog = null;
    let crew = null;
    let ship = null;
    let wheel = 0;
    let frame = null;
    let last = 0;
    let time = 0;
    let nearby = [];
    let collected = new Map();
    let visited = new Map();
    let earned = new Set();
    let mission = null;
    let missionSeed = 1;
    let stats = null;
    let lastCatchAt = 0;
    let lastRareToastAt = -Infinity;
    let lastInputAt = 0;
    let isOffCourse = false;
    let toastId = 0;
    const sound = createSound();
    const timers = {
        nearby : 0,
        draw : 0,
        fog : 0,
        slow : 0,
        save : 0
    };

    function freshStats() {
        return {
            shovels : 0,
            bumps : 0,
            valves : 0,
            missions : 0,
            crossedEquator : false
        };
    }

    function iconOf(specimen) {
        return `sp|${ICON_KEYS.get(groupIcon(specimen.group)) ?? 'unknown'}|${specimen.rarity}`;
    }

    function addToast(toast) {
        const id = ++toastId;
        const item = {
            ...toast,
            id
        };

        toasts.value = [...toasts.value, item].slice(-MAX_TOASTS);
        setTimeout(() => {
            toasts.value = toasts.value.filter((entry) => entry.id !== id);
        }, (TOAST_SECONDS[toast.kind] ?? 4) * 1000);
    }

    function say(event, values, extra) {
        const line = crew?.say(event, values, extra);

        if (line) {
            addToast({
                kind : 'crew',
                title : line.name,
                text : line.text,
                portrait : line.portrait,
                emoji : line.emoji,
                photo : line.photo ?? null
            });
        }
    }

    function gameStats() {
        const rarities = new Set();
        const groups = new Set();
        let nameBearers = 0;
        let algae = 0;

        for (const id of collected.keys()) {
            const specimen = data.byId.get(id);

            if (!specimen) {
                continue;
            }

            rarities.add(specimen.rarity);
            groups.add(specimen.group);
            nameBearers += specimen.rarity === 'nameBearer' ? 1 : 0;
            algae += ALGAE.has(specimen.group) ? 1 : 0;
        }

        return {
            ...stats,
            collected : collected.size,
            nameBearers,
            rarities,
            groups,
            algae,
            stations : visited.size,
            discovered : fog?.share() ?? 0
        };
    }

    function checkAchievements() {
        for (const achievement of newAchievements(gameStats(), earned)) {
            earned.add(achievement.id);
            sound.ting();
            addToast({
                kind : 'achievement',
                title : `Insigne: ${achievement.title}`,
                text : achievement.text,
                emoji : '🏅'
            });
        }
    }

    function missingGroups() {
        const have = new Set([...collected.keys()].map((id) => data.byId.get(id)?.group));

        return new Set(data.groups.filter((group) => !have.has(group)));
    }

    function newMission(group = null) {
        mission = createMission({
            ship,
            specimens : data.specimens,
            collected,
            grid,
            group,
            missingGroups : missingGroups(),
            seed : missionSeed++
        });

        if (!mission && group) {
            addToast({
                kind : 'note',
                title : 'Niets gevonden',
                text : `Er drijft geen ${groupName(group).toLowerCase()} meer binnen bereik. Hier is een andere missie.`,
                emoji : '🧭'
            });
            mission = createMission({
                ship,
                specimens : data.specimens,
                collected,
                grid,
                missingGroups : missingGroups(),
                seed : missionSeed++
            });
        }

        map.value?.setTarget(mission);
        updateMission();
    }

    function updateMission() {
        if (!mission) {
            missionView.value = null;

            return;
        }

        const distance = distanceKm(ship, mission.center);

        // Sailed far away from it: a new mission closer by
        if (distance > MISSION_GIVE_UP_KM) {
            newMission();

            return;
        }

        missionView.value = {
            text : mission.text,
            person : crew.person(mission.giver),
            bearing : Math.round(bearingTo(ship, mission.center)),
            distance : Math.round(distance),
            inside : distance < mission.radiusKm
        };
    }

    // The uncollected specimens near the ship, again every half second
    function findNearby() {
        nearby = data.specimens.filter((specimen) => !collected.has(specimen.id) && Math.abs(specimen.place.lat - ship.lat) < 2.5 && distanceKm(ship, specimen.place) < NEAR_KM);
    }

    function catchSpecimen(specimen, point) {
        const points = pointsOf(specimen);
        const isTarget = mission?.specimenId === specimen.id;
        const isFirstOfRarity = ![...collected.keys()].some((id) => data.byId.get(id)?.rarity === specimen.rarity);
        const screen = map.value?.project(point);

        collected.set(specimen.id, Date.now());
        collectedCount.value = collected.size;
        score.value += points * (isTarget ? 2 : 1);
        lastCatchAt = time;

        if (screen) {
            hud.value?.fly(screen, specimen.rarity);
        }

        map.value?.splash(point, RARITIES[specimen.rarity].color);
        sound.splash();
        sound.pling(specimen.rarity === 'rare' || specimen.rarity === 'nameBearer');
        navigator.vibrate?.(specimen.rarity === 'nameBearer' ? [30, 40, 60] : 25);

        const isSpecial = specimen.rarity === 'rare' || specimen.rarity === 'nameBearer';

        // A message for the first of every rarity; later rare ones and name bearers now and then
        if (isFirstOfRarity || (isSpecial && time - lastRareToastAt > RARE_TOAST_SECONDS)) {
            const museum = specimen.museum?.stad ?? specimen.museum?.naam;

            lastRareToastAt = time;
            addToast({
                kind : 'specimen',
                title : `${isFirstOfRarity ? 'Nieuw: ' : ''}${specimen.name ?? 'onbekende soort'}`,
                text : `${groupName(specimen.group)} · ${RARITIES[specimen.rarity].label}${museum ? ` · ligt nu in ${museum}` : ''}`,
                group : specimen.group,
                color : RARITIES[specimen.rarity].color,
                specimenId : specimen.id
            });
        }

        if (collected.size === 1) {
            say('firstCatch');
        } else if (specimen.rarity === 'nameBearer' && isFirstOfRarity) {
            say('nameBearer', {
                name : specimen.name ?? 'deze soort'
            });
        } else if (MILESTONES.includes(collected.size)) {
            say('milestone', {
                count : collected.size.toLocaleString('nl-NL')
            });
        } else if (specimen.rarity === 'rare') {
            say('rare', {
                name : specimen.name ?? 'deze soort'
            });
        } else if (ALGAE.has(specimen.group)) {
            say('algae');
        }

        if (isTarget) {
            stats.missions++;
            say('missionDone', {
                giver : mission.giver
            });
            mission = null;
            map.value?.setTarget(null);
            missionView.value = null;
            setTimeout(() => {
                if (!mission && ship) {
                    newMission();
                }
            }, 3000);
        }

        checkAchievements();
    }

    // Moves the specimens near the ship a little, pulls in the close ones and catches what is in reach
    function updateSpecimens(dt, isDrawing) {
        const features = [];

        for (const specimen of nearby) {
            if (collected.has(specimen.id)) {
                continue;
            }

            const drift = moveKm(specimen.place, Math.sin(time * 0.31 + specimen.phase) * DRIFT_KM, Math.cos(time * 0.23 + specimen.phase * 1.3) * DRIFT_KM);
            const distance = distanceKm(ship, drift);
            const magnet = specimen.attract ? STATION_MAGNET_KM : MAGNET_KM;

            specimen.pull = Math.max(0, Math.min(1, (specimen.pull ?? 0) + (distance < magnet ? dt * 0.9 : -dt * 0.5)));

            const point = specimen.pull ? {
                lon : drift.lon + (ship.lon - drift.lon) * specimen.pull * specimen.pull,
                lat : drift.lat + (ship.lat - drift.lat) * specimen.pull * specimen.pull
            } : drift;

            if (distanceKm(ship, point) < CATCH_KM) {
                catchSpecimen(specimen, point);
                continue;
            }

            if (isDrawing) {
                const isSpecial = specimen.rarity === 'rare' || specimen.rarity === 'nameBearer';

                features.push({
                    type : 'Feature',
                    properties : {
                        icon : iconOf(specimen),
                        size : (specimen.rarity === 'nameBearer' ? 1.2 : 1) * (isSpecial ? 1 + 0.1 * Math.sin(time * 5 + specimen.phase) : 1),
                        order : ['common', 'uncommon', 'rare', 'nameBearer'].indexOf(specimen.rarity)
                    },
                    geometry : {
                        type : 'Point',
                        coordinates : [point.lon, point.lat]
                    }
                });
            }
        }

        if (isDrawing) {
            map.value?.setSpecimens(features);
        }
    }

    function visitStations() {
        for (const station of data.stations) {
            if (visited.has(station.nummer) || Math.abs(station.lat - ship.lat) > 0.3 || distanceKm(ship, station) > STATION_KM) {
                continue;
            }

            visited.set(station.nummer, Date.now());
            map.value?.setVisited(station.index);
            sound.bell();

            // The real catch of this station comes to the ship
            for (const specimen of station.specimens) {
                specimen.attract = true;
            }

            if (station.photo) {
                say('stationPhoto', {
                    station : station.nummer,
                    caption : station.photo.caption
                }, {
                    photo : station.photo.thumb
                });
            } else {
                say('station', {
                    station : station.nummer,
                    date : new Date(`${station.datum}T12:00:00Z`).toLocaleDateString('nl-NL', {
                        day : 'numeric',
                        month : 'long',
                        year : 'numeric'
                    })
                });
            }

            checkAchievements();
        }
    }

    // When nothing is near for a while, the compass points to the nearest station not yet visited
    function updateCompass() {
        let nearest = null;
        let nearestKm = Infinity;

        for (const station of data.stations) {
            if (visited.has(station.nummer)) {
                continue;
            }

            const distance = distanceKm(ship, station);

            if (distance < nearestKm) {
                nearest = station;
                nearestKm = distance;
            }
        }

        const wasOffCourse = isOffCourse;

        isOffCourse = Boolean(nearest) && (nearestKm > OFF_COURSE_KM || (time - lastCatchAt > QUIET_SECONDS && nearestKm > STATION_KM * 2));
        compass.value = isOffCourse ? {
            bearing : Math.round(bearingTo(ship, nearest)),
            distance : Math.round(nearestKm),
            station : nearest.nummer
        } : null;

        if (isOffCourse && !wasOffCourse && nearestKm > OFF_COURSE_KM) {
            say('offCourse', {
                distance : Math.round(nearestKm)
            });
        }
    }

    function crossEquator() {
        stats.crossedEquator = true;
        sound.bell();
        sound.splash();
        equator.value = {
            lon : ship.lon,
            at : Date.now()
        };
        checkAchievements();
    }

    function onShovel() {
        if (!ship || isPaused.value) {
            return;
        }

        shovel(ship);
        stats.shovels++;
        lastInputAt = time;
        sound.shovel();

        if (stats.shovels === 30) {
            say('stoking');
        }

        if (stats.shovels === 100) {
            checkAchievements();
        }
    }

    function onTurn(value) {
        wheel = value;

        if (Math.abs(value) > 0.05) {
            lastInputAt = time;
        }
    }

    function tick(now) {
        frame = requestAnimationFrame(tick);

        const dt = Math.min(0.05, (now - last) / 1000 || 0);

        last = now;

        if (isPaused.value || !ship) {
            return;
        }

        time += dt;

        const previousLat = ship.lat;
        const events = step(ship, wheel, dt, land);

        for (const event of events) {
            if (event === 'valve') {
                stats.valves++;
                isVenting.value = true;
                setTimeout(() => {
                    isVenting.value = false;
                }, 1400);
                sound.steam();
                say('valve');
                checkAchievements();
            } else if (event === 'bump') {
                stats.bumps++;
                sound.bump();
                map.value?.shake();
                navigator.vibrate?.(60);
                say('bump');

                if (stats.bumps === 10) {
                    checkAchievements();
                }
            }
        }

        const level = (ship.pressure - PRESSURE_FLOOR) / (1 - PRESSURE_FLOOR);

        pressure.value = ship.pressure;
        map.value?.update(ship, dt, level);
        sound.setWaves(level);

        if (!stats.crossedEquator && Math.sign(previousLat) !== Math.sign(ship.lat)) {
            crossEquator();
        }

        timers.nearby += dt;
        timers.draw += dt;
        timers.fog += dt;
        timers.slow += dt;
        timers.save += dt;

        if (timers.nearby > 0.5) {
            timers.nearby = 0;
            findNearby();
        }

        const isDrawing = timers.draw > 1 / 12;

        if (isDrawing) {
            timers.draw = 0;
        }

        updateSpecimens(dt, isDrawing);

        if (timers.fog > 0.25) {
            timers.fog = 0;

            if (fog.reveal(ship)) {
                map.value?.refreshFog();
                discovered.value = fog.share();
            }

            visitStations();
            updateMission();
        }

        if (timers.slow > 1) {
            timers.slow = 0;
            updateCompass();
            checkAchievements();

            if (time - lastInputAt > IDLE_SECONDS) {
                lastInputAt = time;
                say('idle');
            }
        }

        if (timers.save > SAVE_SECONDS) {
            timers.save = 0;
            save();
        }
    }

    function save() {
        if (!ship) {
            return;
        }

        saveProgress({
            ship : {
                lon : ship.lon,
                lat : ship.lat,
                heading : ship.heading
            },
            score : score.value,
            collected : [...collected],
            visited : [...visited],
            fog : fog.encode(),
            achievements : [...earned],
            mission,
            missionSeed,
            stats
        });
    }

    function startGame(isNew) {
        sound.unlock();
        sound.setMuted(isMuted.value);

        const saved = isNew ? null : loadProgress();

        if (isNew) {
            clearProgress();
        }

        ship = createShip(saved?.ship ?? start.value);
        collected = new Map(saved?.collected ?? []);
        visited = new Map(saved?.visited ?? []);
        earned = new Set(saved?.achievements ?? []);
        stats = {
            ...freshStats(),
            ...(saved?.stats ?? {})
        };
        score.value = saved?.score ?? 0;
        missionSeed = saved?.missionSeed ?? 1;
        collectedCount.value = collected.size;
        time = 0;
        lastCatchAt = 0;
        lastInputAt = 0;

        for (const specimen of data.specimens) {
            specimen.pull = 0;
            specimen.attract = false;
        }

        if (isNew) {
            fog.reset();
        }

        fog.restore(saved?.fog);
        fog.reveal(ship);
        discovered.value = fog.share();
        phase.value = 'playing';

        // The map exists once the game is ready; give it a frame to get its sources
        requestAnimationFrame(() => {
            map.value?.refreshFog();

            for (const nummer of visited.keys()) {
                const station = data.stations.find((item) => item.nummer === nummer);

                if (station) {
                    map.value?.setVisited(station.index);
                }
            }

            findNearby();

            if (saved?.mission && !collected.has(saved.mission.specimenId)) {
                mission = saved.mission;
                map.value?.setTarget(mission);
                updateMission();
            } else {
                newMission();
            }
        });

        if (!saved) {
            say('welcome');
        }
    }

    function openAlbum(focus = null) {
        album.value = {
            collected : Object.fromEntries(collected),
            visited : [...visited]
                .sort((a, b) => b[1] - a[1])
                .map(([nummer]) => data.stations.find((station) => station.nummer === nummer))
                .filter(Boolean),
            achievements : ACHIEVEMENTS.map((achievement) => ({
                ...achievement,
                earned : earned.has(achievement.id)
            })),
            focus
        };
    }

    function onSeek(group) {
        album.value = null;
        newMission(group);
    }

    function onToast(toast) {
        if (toast.specimenId) {
            openAlbum(toast.specimenId);
        } else if (toast.kind === 'achievement') {
            openAlbum();
        }

        toasts.value = toasts.value.filter((entry) => entry.id !== toast.id);
    }

    function toggleMute() {
        isMuted.value = !isMuted.value;
        sound.unlock();
        sound.setMuted(isMuted.value);
        saveMuted(isMuted.value);
    }

    function onVisibility() {
        if (document.hidden) {
            save();
        }
    }

    // The first point of the route out of Surabaya with open water all around, so the ship does not
    // start in the narrow harbour channel, which the land mask closes
    function openWaterStart(line) {
        const isOpen = (point) => !land.isLand(point) && [0, 45, 90, 135, 180, 225, 270, 315].every((angle) => {
            const radians = angle * Math.PI / 180;

            return !land.isLand(moveKm(point, Math.sin(radians) * START_CLEARANCE_KM, Math.cos(radians) * START_CLEARANCE_KM));
        });

        for (let km = 0; km < 400; km += 2) {
            const point = pointAt(line, km);

            if (isOpen(point)) {
                return {
                    lon : point.lon,
                    lat : point.lat,
                    heading : point.bearing
                };
            }
        }

        const first = pointAt(line, 0);

        return {
            ...(land.nearestWater(first) ?? first),
            heading : first.bearing
        };
    }

    async function prepare() {
        loadingText.value = 'Specimens ophalen…';

        const game = await loadGame();

        loadingText.value = 'Kaart tekenen…';
        // Let the text show before the heavy work; a timeout also runs in a tab in the background
        await new Promise((resolve) => setTimeout(resolve, 20));
        land = createLandMask(toRaw(store.mapLayers)?.land);
        grid = createWaterGrid(land);
        assignRarities(game.specimens);
        placeSpecimens(game.specimens, game.stations, game.line, land);
        fog = await createFog(grid);

        start.value = openWaterStart(game.line);
        data = {
            ...game,
            byId : new Map(game.specimens.map((specimen) => [specimen.id, specimen]))
        };
        crew = createCrew(store.data?.records);
        total.value = game.specimens.length;
        gameStations.value = game.stations;
        gameLine.value = game.line;
        fogCanvas.value = fog.canvas;
        hasSave.value = Boolean(loadProgress());
        phase.value = 'intro';
    }

    onMounted(async () => {
        document.addEventListener('visibilitychange', onVisibility);
        frame = requestAnimationFrame(tick);

        // For testing in the browser console during development only
        if (import.meta.env.DEV) {
            window.sibogaGame = {
                get ship() {
                    return ship;
                },
                teleport(lon, lat) {
                    Object.assign(ship, {
                        lon,
                        lat
                    });
                }
            };
        }

        try {
            await prepare();
        } catch (error) {
            console.error(error);
            loadingText.value = 'Het spel kon niet laden. Probeer het later nog eens.';
        }
    });

    onBeforeUnmount(() => {
        save();
        cancelAnimationFrame(frame);
        document.removeEventListener('visibilitychange', onVisibility);
        sound.close();
    });
</script>

<template>
    <div class="el-game">
        <el-game-map
            v-if="start"
            ref="map"
            v-bind:stations="gameStations"
            v-bind:line="gameLine"
            v-bind:start="start"
            v-bind:fog-canvas="fogCanvas" />

        <template v-if="phase === 'playing'">
            <el-game-hud
                ref="hud"
                v-bind:score="score"
                v-bind:collected="collectedCount"
                v-bind:total="total"
                v-bind:discovered="discovered"
                v-bind:mission="missionView"
                v-bind:compass="compass"
                v-bind:is-muted="isMuted"
                v-bind:toasts="toasts"
                v-on:album="openAlbum()"
                v-on:info="isInfoOpen = true"
                v-on:mute="toggleMute()"
                v-on:skip="newMission()"
                v-on:toast="onToast($event)" />

            <div class="controls">
                <el-game-boiler
                    class="controls__boiler"
                    v-bind:pressure="pressure"
                    v-bind:is-venting="isVenting"
                    v-on:shovel="onShovel()" />
                <el-game-helm
                    class="controls__helm"
                    v-on:turn="onTurn($event)" />
            </div>
        </template>

        <div
            v-if="phase === 'loading'"
            class="loading">{{ loadingText }}</div>

        <el-game-intro
            v-if="phase === 'intro' || isInfoOpen"
            v-bind:has-save="hasSave"
            v-bind:is-info="isInfoOpen"
            v-on:start="startGame($event)"
            v-on:close="isInfoOpen = false" />

        <el-game-album
            v-if="album"
            v-bind:specimens="data.specimens"
            v-bind:collected="album.collected"
            v-bind:visited="album.visited"
            v-bind:achievements="album.achievements"
            v-bind:focus="album.focus"
            v-on:close="album = null"
            v-on:seek="onSeek($event)" />

        <el-game-equator
            v-if="equator"
            v-bind:lon="equator.lon"
            v-bind:at="equator.at"
            v-on:close="equator = null" />
    </div>
</template>

<style lang="scss" scoped>
    .el-game {
        position: absolute;
        inset: 0;
        overflow: hidden;
        background: var(--c-sea);
        user-select: none;
        -webkit-user-select: none;
    }

    .controls {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 6;
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        padding: 0 1.2rem max(1.2rem, env(safe-area-inset-bottom));
        pointer-events: none;

        > * {
            pointer-events: auto;
        }
    }

    .loading {
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        padding: 1.2rem 2rem;
        border-radius: 0.8rem;
        background: var(--c-paper);
        box-shadow: var(--shadow-float);
        font-size: 1.6rem;
    }
</style>
