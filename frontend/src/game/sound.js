// The sounds of the game, all made with Web Audio on the spot, so there are no sound files and no
// licences: the ship's bell, splashes, the shovel, the safety valve, a bump and the sea itself.
// Browsers only allow sound after a tap, so unlock() runs on the first one.
export function createSound() {
    let context = null;
    let master = null;
    let noise = null;
    let waves = null;
    let isMuted = false;

    function noiseBuffer() {
        const buffer = context.createBuffer(1, context.sampleRate * 2, context.sampleRate);
        const data = buffer.getChannelData(0);

        for (let i = 0; i < data.length; i++) {
            data[i] = Math.random() * 2 - 1;
        }

        return buffer;
    }

    function envelope(gain, at, attack, peak, decay) {
        gain.gain.setValueAtTime(0.0001, at);
        gain.gain.exponentialRampToValueAtTime(peak, at + attack);
        gain.gain.exponentialRampToValueAtTime(0.0001, at + attack + decay);
    }

    function tone(frequency, { type = 'sine', peak = 0.3, attack = 0.005, decay = 0.6, delay = 0, slideTo = null } = {}) {
        if (!context || isMuted) {
            return;
        }

        const at = context.currentTime + delay;
        const oscillator = context.createOscillator();
        const gain = context.createGain();

        oscillator.type = type;
        oscillator.frequency.setValueAtTime(frequency, at);

        if (slideTo) {
            oscillator.frequency.exponentialRampToValueAtTime(slideTo, at + attack + decay);
        }

        envelope(gain, at, attack, peak, decay);
        oscillator.connect(gain).connect(master);
        oscillator.start(at);
        oscillator.stop(at + attack + decay + 0.05);
    }

    function hiss({ filter = 'bandpass', frequency = 1200, q = 0.8, peak = 0.3, attack = 0.01, decay = 0.4, delay = 0 } = {}) {
        if (!context || isMuted) {
            return;
        }

        const at = context.currentTime + delay;
        const source = context.createBufferSource();
        const shape = context.createBiquadFilter();
        const gain = context.createGain();

        source.buffer = noise;
        shape.type = filter;
        shape.frequency.value = frequency;
        shape.Q.value = q;
        envelope(gain, at, attack, peak, decay);
        source.connect(shape).connect(gain).connect(master);
        source.start(at, Math.random());
        source.stop(at + attack + decay + 0.05);
    }

    // A bronze bell: a few partials that are not quite in tune, ringing out slowly
    function bell() {
        for (const [ratio, peak] of [[1, 0.28], [2.01, 0.16], [2.76, 0.12], [5.4, 0.06]]) {
            tone(660 * ratio, {
                peak,
                attack : 0.003,
                decay : 2.2 / ratio + 0.4
            });
            tone(660 * ratio, {
                peak : peak * 0.6,
                attack : 0.003,
                decay : 2 / ratio + 0.3,
                delay : 0.55
            });
        }
    }

    function bump() {
        tone(110, {
            type : 'triangle',
            peak : 0.5,
            decay : 0.3,
            slideTo : 45
        });
        hiss({
            filter : 'lowpass',
            frequency : 400,
            peak : 0.25,
            decay : 0.2
        });
    }

    function pling(isSpecial) {
        tone(isSpecial ? 1320 : 990, {
            peak : 0.18,
            decay : 0.35
        });
        tone(isSpecial ? 1980 : 1485, {
            peak : 0.1,
            decay : 0.3,
            delay : 0.07
        });
    }

    function setMuted(value) {
        isMuted = value;

        if (master) {
            master.gain.value = value ? 0 : 0.8;
        }
    }

    function setWaves(level) {
        if (waves) {
            waves.gain.setTargetAtTime(isMuted ? 0 : 0.02 + 0.06 * level, context.currentTime, 0.4);
        }
    }

    function shovel() {
        hiss({
            filter : 'highpass',
            frequency : 2500,
            peak : 0.12,
            decay : 0.12
        });
        tone(180, {
            type : 'square',
            peak : 0.05,
            decay : 0.08,
            delay : 0.1
        });
    }

    function splash() {
        hiss({
            frequency : 900,
            q : 0.5,
            peak : 0.3,
            attack : 0.005,
            decay : 0.35
        });
    }

    function steam() {
        hiss({
            filter : 'highpass',
            frequency : 3000,
            peak : 0.25,
            attack : 0.05,
            decay : 1.4
        });
    }

    function ting() {
        tone(1760, {
            peak : 0.2,
            decay : 0.9
        });
        tone(2637, {
            peak : 0.12,
            decay : 0.7,
            delay : 0.12
        });
    }

    // Starts the audio on the first tap; the sea rustles from then on
    function unlock() {
        if (context) {
            context.resume?.();

            return;
        }

        const Context = window.AudioContext ?? window.webkitAudioContext;

        if (!Context) {
            return;
        }

        context = new Context();
        master = context.createGain();
        master.gain.value = isMuted ? 0 : 0.8;
        master.connect(context.destination);
        noise = noiseBuffer();

        const source = context.createBufferSource();
        const shape = context.createBiquadFilter();

        waves = context.createGain();
        waves.gain.value = 0;
        source.buffer = noise;
        source.loop = true;
        shape.type = 'lowpass';
        shape.frequency.value = 500;
        source.connect(shape).connect(waves).connect(master);
        source.start();
    }

    function close() {
        context?.close?.();
        context = null;
    }

    return {
        bell,
        bump,
        close,
        pling,
        setMuted,
        setWaves,
        shovel,
        splash,
        steam,
        ting,
        unlock
    };
}
