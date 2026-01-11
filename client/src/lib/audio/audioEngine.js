export class AudioEngine {
  constructor() {
    this.audioContext = null;
    this.atcAudioElement = null;
    this.musicAudioElement = null;
    this.atcSource = null;
    this.musicSource = null;
    this.atcGainNode = null;
    this.musicGainNode = null;
    this.masterGainNode = null;
    this.isInitialized = false;
  }

  async init() {
    if (this.isInitialized) return;

    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

      this.atcAudioElement = new Audio();
      this.atcAudioElement.crossOrigin = 'anonymous';

      this.musicAudioElement = new Audio();
      this.musicAudioElement.crossOrigin = 'anonymous';

      this.atcSource = this.audioContext.createMediaElementSource(this.atcAudioElement);
      this.musicSource = this.audioContext.createMediaElementSource(this.musicAudioElement);

      this.atcGainNode = this.audioContext.createGain();
      this.musicGainNode = this.audioContext.createGain();
      this.masterGainNode = this.audioContext.createGain();

      this.atcSource.connect(this.atcGainNode);
      this.musicSource.connect(this.musicGainNode);

      this.atcGainNode.connect(this.masterGainNode);
      this.musicGainNode.connect(this.masterGainNode);

      this.masterGainNode.connect(this.audioContext.destination);

      this.atcGainNode.gain.value = 0.7;
      this.musicGainNode.gain.value = 0.5;
      this.masterGainNode.gain.value = 1.0;

      this.isInitialized = true;
      console.log('Audio engine initialized');
    } catch (error) {
      console.error('Failed to initialize audio engine:', error);
      throw error;
    }
  }

  async playAtc(streamUrl) {
    if (!this.isInitialized) await this.init();

    try {
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      this.atcAudioElement.src = streamUrl;
      await this.atcAudioElement.play();
      console.log('Playing ATC stream:', streamUrl);
    } catch (error) {
      console.error('Failed to play ATC stream:', error);
      throw error;
    }
  }

  async playMusic(streamUrl) {
    if (!this.isInitialized) await this.init();

    try {
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      this.musicAudioElement.src = streamUrl;
      await this.musicAudioElement.play();
      console.log('Playing music stream:', streamUrl);
    } catch (error) {
      console.error('Failed to play music stream:', error);
      throw error;
    }
  }

  pause() {
    if (this.atcAudioElement && !this.atcAudioElement.paused) {
      this.atcAudioElement.pause();
    }
    if (this.musicAudioElement && !this.musicAudioElement.paused) {
      this.musicAudioElement.pause();
    }
  }

  async resume() {
    try {
      if (this.audioContext && this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      const promises = [];
      if (this.atcAudioElement && this.atcAudioElement.paused && this.atcAudioElement.src) {
        promises.push(this.atcAudioElement.play());
      }
      if (this.musicAudioElement && this.musicAudioElement.paused && this.musicAudioElement.src) {
        promises.push(this.musicAudioElement.play());
      }

      await Promise.all(promises);
    } catch (error) {
      console.error('Failed to resume playback:', error);
      throw error;
    }
  }

  isPaused() {
    const atcPaused = !this.atcAudioElement || this.atcAudioElement.paused || !this.atcAudioElement.src;
    const musicPaused = !this.musicAudioElement || this.musicAudioElement.paused || !this.musicAudioElement.src;
    return atcPaused && musicPaused;
  }

  stopAtc() {
    if (this.atcAudioElement) {
      this.atcAudioElement.pause();
      this.atcAudioElement.currentTime = 0;
    }
  }

  stopMusic() {
    if (this.musicAudioElement) {
      this.musicAudioElement.pause();
      this.musicAudioElement.currentTime = 0;
    }
  }

  setAtcVolume(value) {
    if (this.atcGainNode) {
      this.atcGainNode.gain.setValueAtTime(value, this.audioContext.currentTime);
    }
  }

  setMusicVolume(value) {
    if (this.musicGainNode) {
      this.musicGainNode.gain.setValueAtTime(value, this.audioContext.currentTime);
    }
  }

  setMasterVolume(value) {
    if (this.masterGainNode) {
      this.masterGainNode.gain.setValueAtTime(value, this.audioContext.currentTime);
    }
  }

  getAtcVolume() {
    return this.atcGainNode ? this.atcGainNode.gain.value : 0.7;
  }

  getMusicVolume() {
    return this.musicGainNode ? this.musicGainNode.gain.value : 0.5;
  }

  async switchAtcStation(streamUrl, fadeDuration = 0.5) {
    if (!this.atcGainNode) return;

    const targetVolume = this.getAtcVolume();
    const currentTime = this.audioContext.currentTime;
    this.atcGainNode.gain.linearRampToValueAtTime(0, currentTime + fadeDuration / 2);

    setTimeout(async () => {
      await this.playAtc(streamUrl);
      const resumeTime = this.audioContext.currentTime;
      this.atcGainNode.gain.linearRampToValueAtTime(targetVolume, resumeTime + fadeDuration / 2);
    }, (fadeDuration / 2) * 1000);
  }

  async switchMusicSource(streamUrl, fadeDuration = 0.5) {
    if (!this.musicGainNode) return;

    const targetVolume = this.getMusicVolume();
    const currentTime = this.audioContext.currentTime;
    this.musicGainNode.gain.linearRampToValueAtTime(0, currentTime + fadeDuration / 2);

    setTimeout(async () => {
      await this.playMusic(streamUrl);
      const resumeTime = this.audioContext.currentTime;
      this.musicGainNode.gain.linearRampToValueAtTime(targetVolume, resumeTime + fadeDuration / 2);
    }, (fadeDuration / 2) * 1000);
  }

  destroy() {
    this.stopAtc();
    this.stopMusic();
    if (this.audioContext) {
      this.audioContext.close();
    }
    this.isInitialized = false;
  }
}
