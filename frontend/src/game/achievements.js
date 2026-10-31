// The badges of the game: when each one is earned, from the counts of the game so far
import { ACHIEVEMENTS } from './texts.js';

const RULES = {
    first : (stats) => stats.collected >= 1,
    catch10 : (stats) => stats.collected >= 10,
    catch50 : (stats) => stats.collected >= 50,
    catch100 : (stats) => stats.collected >= 100,
    nameBearer : (stats) => stats.nameBearers >= 1,
    allRarities : (stats) => stats.rarities.size >= 4,
    groups5 : (stats) => stats.groups.size >= 5,
    groups10 : (stats) => stats.groups.size >= 10,
    algae10 : (stats) => stats.algae >= 10,
    equator : (stats) => stats.crossedEquator,
    stations10 : (stats) => stats.stations >= 10,
    stations50 : (stats) => stats.stations >= 50,
    discovered25 : (stats) => stats.discovered >= 0.25,
    discovered50 : (stats) => stats.discovered >= 0.5,
    stoker : (stats) => stats.shovels >= 100,
    valve : (stats) => stats.valves >= 1,
    beachcomber : (stats) => stats.bumps >= 10,
    mission1 : (stats) => stats.missions >= 1,
    mission5 : (stats) => stats.missions >= 5,
    mission10 : (stats) => stats.missions >= 10
};

// The badges that the counts earn and that were not earned before
export function newAchievements(stats, earned) {
    return ACHIEVEMENTS.filter((achievement) => !earned.has(achievement.id) && RULES[achievement.id]?.(stats));
}
