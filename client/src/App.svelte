<script>
  import { onMount, onDestroy } from 'svelte';
  import { AudioEngine } from './lib/audio/audioEngine.js';
  import { getAtcStations, getMusicSources, getProxyUrl, getMusicStreamUrl } from './lib/api.js';
  import StationSelector from './lib/components/StationSelector.svelte';
  import MusicSelector from './lib/components/MusicSelector.svelte';
  import VolumeControl from './lib/components/VolumeControl.svelte';

  let audioEngine;
  let atcStations = [];
  let musicSources = [];
  let selectedAtcStation = null;
  let selectedMusicSource = null;
  let atcVolume = 0.7;
  let musicVolume = 0.5;
  let isPlaying = false;
  let loading = true;
  let error = null;

  onMount(async () => {
    try {
      audioEngine = new AudioEngine();

      const [stations, sources] = await Promise.all([
        getAtcStations(),
        getMusicSources()
      ]);

      atcStations = stations;
      musicSources = sources;
      loading = false;
    } catch (err) {
      console.error('Failed to load data:', err);
      error = 'Failed to connect to server. Make sure the backend is running on port 3000.';
      loading = false;
    }
  });

  onDestroy(() => {
    if (audioEngine) {
      audioEngine.destroy();
    }
  });

  async function handleAtcStationSelect(station) {
    try {
      if (!isPlaying) {
        await audioEngine.init();
        isPlaying = true;
      }

      const proxiedUrl = getProxyUrl(station.stream_url);

      if (selectedAtcStation) {
        await audioEngine.switchAtcStation(proxiedUrl);
      } else {
        await audioEngine.playAtc(proxiedUrl);
      }

      selectedAtcStation = station;
      error = null;
    } catch (err) {
      console.error('Failed to play ATC station:', err);
      error = 'Failed to play ATC stream. The station might be offline.';
    }
  }

  async function handleMusicSourceSelect(source) {
    try {
      if (!isPlaying) {
        await audioEngine.init();
        isPlaying = true;
      }

      error = 'Starting music stream...';

      const streamUrl = getMusicStreamUrl(source.id);
      console.log('Playing music stream:', source.name);

      if (selectedMusicSource) {
        await audioEngine.switchMusicSource(streamUrl);
      } else {
        await audioEngine.playMusic(streamUrl);
      }

      selectedMusicSource = source;
      error = null;
    } catch (err) {
      console.error('Failed to play music source:', err);
      error = 'Failed to play music stream. The source might be unavailable.';
    }
  }

  function handleAtcVolumeChange(value) {
    atcVolume = value;
    if (audioEngine) {
      audioEngine.setAtcVolume(value);
    }
  }

  function handleMusicVolumeChange(value) {
    musicVolume = value;
    if (audioEngine) {
      audioEngine.setMusicVolume(value);
    }
  }

  function dismissError() {
    error = null;
  }
</script>

<main>
  <div class="container">
    <header>
      <h1 class="title">LOFI ATC RADIO</h1>
      <div class="subtitle">Air Traffic Control × Lofi Beats</div>
      {#if selectedAtcStation || selectedMusicSource}
        <div class="status-bar">
          <div class="status-item">
            <span class="status-label">ATC:</span>
            <span class="status-value">{selectedAtcStation ? selectedAtcStation.airport_code : 'NONE'}</span>
          </div>
          <div class="status-item">
            <span class="status-label">MUSIC:</span>
            <span class="status-value">{selectedMusicSource ? selectedMusicSource.source_type.toUpperCase() : 'NONE'}</span>
          </div>
          <div class="status-indicator" class:active={isPlaying}>
            {isPlaying ? '◉ LIVE' : '◯ STANDBY'}
          </div>
        </div>
      {/if}
    </header>

    {#if loading}
      <div class="loading">
        <div class="spinner"></div>
        <p>Initializing radio systems...</p>
      </div>
    {:else if error}
      <div class="error-banner">
        <span class="error-text">{error}</span>
        <button class="error-dismiss" on:click={dismissError}>×</button>
      </div>
    {/if}

    {#if !loading}
      <div class="controls-section">
        <StationSelector
          stations={atcStations}
          selectedStation={selectedAtcStation}
          onSelect={handleAtcStationSelect}
        />

        <MusicSelector
          sources={musicSources}
          selectedSource={selectedMusicSource}
          onSelect={handleMusicSourceSelect}
        />

        <div class="volume-section">
          <h3 class="section-title">Volume Controls</h3>
          <div class="volume-grid">
            <VolumeControl
              label="ATC Volume"
              value={atcVolume}
              onChange={handleAtcVolumeChange}
            />
            <VolumeControl
              label="Music Volume"
              value={musicVolume}
              onChange={handleMusicVolumeChange}
            />
          </div>
        </div>
      </div>

      <footer>
        <p class="footer-text">
          Powered by <a href="https://liveatc.net" target="_blank">LiveATC.net</a> • Audio streaming via yt-dlp + ffmpeg
        </p>
        <p class="footer-note">
          YouTube streams are re-encoded server-side for seamless mixing.
        </p>
      </footer>
    {/if}
  </div>
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background: #000;
    color: #00ff00;
    font-family: 'Courier New', monospace;
  }

  main {
    min-height: 100vh;
    background: linear-gradient(180deg, #000 0%, #0a0a0a 100%);
  }

  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
  }

  header {
    text-align: center;
    margin-bottom: 3rem;
    padding: 2rem;
    border: 2px solid #00ff00;
    background: #0a0a0a;
    box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
  }

  .title {
    font-size: 3rem;
    margin: 0;
    letter-spacing: 8px;
    text-shadow: 0 0 10px rgba(0, 255, 0, 0.8);
    animation: flicker 3s infinite;
  }

  @keyframes flicker {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.95; }
  }

  .subtitle {
    font-size: 1.2rem;
    margin-top: 0.5rem;
    opacity: 0.8;
    letter-spacing: 3px;
  }

  .status-bar {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 2rem;
    margin-top: 1.5rem;
    padding: 1rem;
    background: #000;
    border: 1px solid #00ff00;
  }

  .status-item {
    display: flex;
    gap: 0.5rem;
  }

  .status-label {
    opacity: 0.6;
  }

  .status-value {
    font-weight: bold;
  }

  .status-indicator {
    font-weight: bold;
    padding: 0.25rem 0.75rem;
    border: 1px solid #00ff00;
  }

  .status-indicator.active {
    background: #00ff00;
    color: #000;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  .loading {
    text-align: center;
    padding: 4rem;
  }

  .spinner {
    width: 50px;
    height: 50px;
    border: 3px solid rgba(0, 255, 0, 0.3);
    border-top-color: #00ff00;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .error-banner {
    background: rgba(255, 0, 0, 0.1);
    border: 2px solid #ff0000;
    color: #ff0000;
    padding: 1rem;
    margin: 1rem 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .error-dismiss {
    background: none;
    border: none;
    color: #ff0000;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0 0.5rem;
  }

  .controls-section {
    margin-top: 2rem;
  }

  .volume-section {
    margin-top: 2rem;
    padding: 1.5rem;
    border: 2px solid #00ff00;
    background: #0a0a0a;
  }

  .section-title {
    color: #00ff00;
    font-size: 1.2rem;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 600;
  }

  .volume-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
  }

  footer {
    margin-top: 3rem;
    padding: 2rem;
    text-align: center;
    border-top: 1px solid #00ff00;
    opacity: 0.6;
  }

  .footer-text {
    margin: 0.5rem 0;
    font-size: 0.9rem;
  }

  .footer-text a {
    color: #00ff00;
    text-decoration: none;
  }

  .footer-text a:hover {
    text-decoration: underline;
  }

  .footer-note {
    margin: 0.5rem 0;
    font-size: 0.8rem;
    opacity: 0.7;
  }
</style>
