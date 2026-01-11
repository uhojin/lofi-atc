<script>
  import { onMount, onDestroy } from 'svelte';
  import { slide } from 'svelte/transition';
  import { AudioEngine } from './lib/audio/audioEngine.js';
  import { getAtcStations, getMusicSources, getProxyUrl, getMusicStreamUrl } from './lib/api.js';
  import Card from './lib/components/ui/card.svelte';
  import Button from './lib/components/ui/button.svelte';
  import Slider from './lib/components/ui/slider.svelte';
  import Sheet from './lib/components/ui/sheet.svelte';
  import { Music, Radio, Volume2, Disc3, Play, Pause, ChevronDown, ChevronUp } from 'lucide-svelte';


  let audioEngine;
  let atcStations = [];
  let musicSources = [];
  let selectedAtcStation = null;
  let selectedMusicSource = null;
  let atcVolume = [0.7];
  let musicVolume = [0.5];
  let isPlaying = false;
  let isPaused = false;
  let loading = true;
  let error = null;
  let showStationSelector = false;
  let showMusicSelector = false;
  let showVolumeControls = false;

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
      audioEngine.setAtcVolume(value[0]);
    }
  }

  function handleMusicVolumeChange(value) {
    musicVolume = value;
    if (audioEngine) {
      audioEngine.setMusicVolume(value[0]);
    }
  }

  function dismissError() {
    error = null;
  }

  function toggleStationSelector() {
    showStationSelector = !showStationSelector;
    showMusicSelector = false;
  }

  function toggleMusicSelector() {
    showMusicSelector = !showMusicSelector;
    showStationSelector = false;
  }

  function handleStationSelectFromModal(station) {
    handleAtcStationSelect(station);
    showStationSelector = false;
  }

  function handleMusicSelectFromModal(source) {
    handleMusicSourceSelect(source);
    showMusicSelector = false;
  }

  async function togglePlayPause() {
    if (!audioEngine || !isPlaying) return;

    try {
      if (isPaused) {
        await audioEngine.resume();
        isPaused = false;
      } else {
        audioEngine.pause();
        isPaused = true;
      }
    } catch (err) {
      console.error('Failed to toggle playback:', err);
      error = 'Failed to toggle playback';
    }
  }
</script>

<main class="min-h-screen flex items-center justify-center p-3 sm:p-4 md:p-6 bg-gradient-to-br from-black via-zinc-950 to-zinc-900">
  {#if loading}
    <div class="flex flex-col items-center gap-4">
        <svg class="w-10 h-10 sm:w-12 sm:h-12 motion-safe:animate-spin text-primary" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}><!-- Icon from Pixel Icon by HackerNoon - https://creativecommons.org/licenses/by/4.0/ --><path fill="currentColor" d="M11 20h-1v2H9v1H5v-1H4v-6h1v-1h1v3h2v-1h2v-1h2v-1h2v2h-1v1h-2z"/><path fill="currentColor" d="M22 9V7h-1V5h-1V4h-1V3h-2V2h-2V1H9v1H7v1H5v1H4v1H3v2H2v2H1v6h1v1h1v-1h1v-1h3v2h2v-1h2v-1h-1v-1H8v-1h3v1h2v1h2v4h-1v1h-2v2h-1v2h4v-1h2v-1h2v-1h1v-1h1v-2h1v-2h1V9zm-7-2h3v1h1v2h-1V9h-1V8h-2zm-1 2h2v2h-2zm-4 1H8V8h2zm1-2V7h-1V6H8v1H6V6h1V5h4v1h1v1h1v1z"/></svg>
      <p class="text-sm text-muted-foreground">Loading...</p>
    </div>
  {:else}
    <div class="w-full max-w-sm md:max-w-md lg:max-w-lg">
      <Card class="p-4 sm:p-6 md:p-8 space-y-4 sm:space-y-5 md:space-y-6 border-zinc-800 shadow-2xl">
        <div class="space-y-1 sm:space-y-2 text-center">
          <h1 class="text-xl sm:text-2xl md:text-3xl font-bold tracking-tight">Lofi ATC Radio</h1>
          <p class="text-xs sm:text-sm text-muted-foreground">Mix lofi beats with live air traffic control</p>
        </div>

        <div class="relative">
          <button
            class="aspect-square w-full overflow-hidden rounded-lg bg-muted relative group cursor-pointer border border-zinc-800 hover:border-zinc-700 transition-colors"
            on:click={toggleMusicSelector}
            type="button"
          >
            {#if selectedMusicSource?.thumbnail}
              <img
                src={selectedMusicSource.thumbnail}
                alt={selectedMusicSource.name}
                class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              />
              <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                <svg class="w-16 h-16 text-white opacity-0 group-hover:opacity-100 transition-opacity" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}><!-- Icon from Pixel Icon by HackerNoon - https://creativecommons.org/licenses/by/4.0/ --><path fill="currentColor" d="M23 1v17h-1v1h-1v1h-4v-1h-1v-1h-1v-3h1v-1h1v-1h3V8h-2v1h-3v1h-4v1H9v10H8v1H7v1H3v-1H2v-1H1v-3h1v-1h1v-1h3V6h2V5h3V4h4V3h3V2h3V1z"/></svg>
                <!-- <svg class="w-10 h-10 sm:w-12 sm:h-12 text-white opacity-0 group-hover:opacity-100 transition-opacity" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}>Icon from Pixel Icon by HackerNoon - https://creativecommons.org/licenses/by/4.0/<path fill="currentColor" d="M21 1v1h-3v1h-3v1h-4v1H8v1H6v10H3v1H2v1H1v3h1v1h1v1h4v-1h1v-1h1V11h2v-1h4V9h3V8h2v5h-3v1h-1v1h-1v3h1v1h1v1h4v-1h1v-1h1V1zM3 21v-3h4v3zM18 6v1h-3v1h-4v1H8V7h3V6h4V5h3V4h3v2zm-1 12v-3h4v3z"/></svg> -->
              </div>
            {:else}
              <div class="w-full h-full flex flex-col items-center justify-center text-muted-foreground">
                <!-- <Music class="w-12 h-12 sm:w-16 sm:h-16 mb-2" /> -->
                 <svg class="w-12 h-12 sm:w-16 sm:h-16 mb-2" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}><!-- Icon from Pixel Icon by HackerNoon - https://creativecommons.org/licenses/by/4.0/ --><path fill="currentColor" d="M21 1v1h-3v1h-3v1h-4v1H8v1H6v10H3v1H2v1H1v3h1v1h1v1h4v-1h1v-1h1V11h2v-1h4V9h3V8h2v5h-3v1h-1v1h-1v3h1v1h1v1h4v-1h1v-1h1V1zM3 21v-3h4v3zM18 6v1h-3v1h-4v1H8V7h3V6h4V5h3V4h3v2zm-1 12v-3h4v3z"/></svg>
                <p class="text-xs sm:text-sm">Select Music Source</p>
              </div>
            {/if}
          </button>

          {#if isPlaying}
            <div class="absolute -bottom-6 left-1/2 -translate-x-1/2 z-10">
              <button
                class="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-primary text-primary-foreground shadow-2xl hover:scale-105 transition-transform active:scale-95 flex items-center justify-center border-4 border-background"
                on:click={togglePlayPause}
                type="button"
                aria-label={isPaused ? 'Play' : 'Pause'}
              >
                {#if isPaused}
                  <!-- <Play class="w-6 h-6 sm:w-7 sm:h-7 ml-0.5" fill="currentColor" /> -->
                  <svg class="w-6 h-6 sm:w-7 sm:h-7 ml-0.5" fill="currentColor" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}><!-- Icon from Pixel Icon by HackerNoon - https://creativecommons.org/licenses/by/4.0/ --><path fill="currentColor" d="M22 11v2h-1v1h-1v1h-2v1h-2v1h-1v1h-2v1h-2v1h-1v1H8v1H6v1H3v-1H2V2h1V1h3v1h2v1h2v1h1v1h2v1h2v1h1v1h2v1h2v1h1v1z"/></svg>
                {:else}
                  <!-- <Pause class="w-6 h-6 sm:w-7 sm:h-7" fill="currentColor" /> -->
                  <svg class="w-6 h-6 sm:w-7 sm:h-7" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}><!-- Icon from Pixel Icon by HackerNoon - https://creativecommons.org/licenses/by/4.0/ --><path fill="currentColor" d="M23 2v20h-1v1h-7v-1h-1V2h1V1h7v1zM9 2h1v20H9v1H2v-1H1V2h1V1h7z"/></svg>
                {/if}
              </button>
            </div>
          {/if}
        </div>

        {#if selectedMusicSource}
          <div class="space-y-0.5 sm:space-y-1 {isPlaying ? 'mt-8' : ''}">
            <h2 class="font-semibold text-sm sm:text-base line-clamp-1">{selectedMusicSource.name}</h2>
            <div class="flex items-center justify-between">
              <p class="text-xs text-muted-foreground uppercase">{selectedMusicSource.source_type}</p>
              {#if isPlaying}
                <div class="flex items-center gap-1.5">
                  <div class="w-1.5 h-1.5 bg-green-500 rounded-full {isPaused ? '' : 'animate-pulse'}"></div>
                  <span class="text-[10px] text-muted-foreground uppercase">{isPaused ? 'Paused' : 'Live'}</span>
                </div>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Inline Volume Controls (Desktop/Tablet) -->
        {#if isPlaying}
          <div class="hidden md:block space-y-4">
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <svg class="w-4 h-4 text-muted-foreground" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}><!-- Icon from Pixel Icon by HackerNoon - https://creativecommons.org/licenses/by/4.0/ --><path fill="currentColor" d="M21 1v1h-3v1h-3v1h-4v1H8v1H6v10H3v1H2v1H1v3h1v1h1v1h4v-1h1v-1h1V11h2v-1h4V9h3V8h2v5h-3v1h-1v1h-1v3h1v1h1v1h4v-1h1v-1h1V1zM3 21v-3h4v3zM18 6v1h-3v1h-4v1H8V7h3V6h4V5h3V4h3v2zm-1 12v-3h4v3z"/></svg>
                  <span class="text-sm font-medium">Music</span>
                </div>
                <span class="text-xs text-muted-foreground tabular-nums">{Math.round(musicVolume[0] * 100)}%</span>
              </div>
              <Slider
                bind:value={musicVolume}
                onValueChange={handleMusicVolumeChange}
                min={0}
                max={1}
                step={0.01}
                class="touch-manipulation"
              />
            </div>

            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <svg class="w-4 h-4 text-muted-foreground" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}><!-- Icon from Pixelarticons by Gerrit Halfmann - https://github.com/halfmage/pixelarticons/blob/master/LICENSE --><path fill="currentColor" d="M19 2h2v2h-2zm2 14V4h2v12zm0 0v2h-2v-2zM1 4h2v12H1zm2 12h2v2H3zM3 4h2V2H3zm2 2h2v8H5zm2 8h2v2H7zm0-8h2V4H7zm10 0h2v8h-2zm0 0h-2V4h2zm0 8v2h-2v-2zm-6-7h4v6h-2v9h-2v-9H9V7zm0 4h2V9h-2z"/></svg>
                  <span class="text-sm font-medium">ATC Radio</span>
                </div>
                <span class="text-xs text-muted-foreground tabular-nums">{Math.round(atcVolume[0] * 100)}%</span>
              </div>
              <Slider
                bind:value={atcVolume}
                onValueChange={handleAtcVolumeChange}
                min={0}
                max={1}
                step={0.01}
                class="touch-manipulation"
              />
            </div>
          </div>
        {/if}

        <Button
          variant="outline"
          class="w-full text-xs sm:text-sm h-9 sm:h-10 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900"
          on:click={toggleStationSelector}
        >           
           <svg class="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-2" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}>Icon from Pixelarticons by Gerrit Halfmann - https://github.com/halfmage/pixelarticons/blob/master/LICENSE<path fill="currentColor" d="M19 2h2v2h-2zm2 14V4h2v12zm0 0v2h-2v-2zM1 4h2v12H1zm2 12h2v2H3zM3 4h2V2H3zm2 2h2v8H5zm2 8h2v2H7zm0-8h2V4H7zm10 0h2v8h-2zm0 0h-2V4h2zm0 8v2h-2v-2zm-6-7h4v6h-2v9h-2v-9H9V7zm0 4h2V9h-2z"/></svg>
          <span class="truncate">
            {selectedAtcStation ? `${selectedAtcStation.airport_code} - ${selectedAtcStation.name}` : 'Select ATC Station'}
          </span>
        </Button>

        {#if error}
          <div class="rounded-lg bg-destructive/10 border border-destructive/20 p-2.5 sm:p-3 text-xs sm:text-sm text-destructive">
            {error}
          </div>
        {/if}
      </Card>
    </div>

    <Sheet bind:open={showMusicSelector} onOpenChange={(open) => showMusicSelector = open}>
      <div class="flex flex-col h-full">
        <div class="flex items-center justify-between mb-4 sm:mb-6">
          <h2 class="text-base sm:text-lg font-semibold">Select Music Source</h2>
          <Button variant="ghost" size="icon" class="h-8 w-8 sm:h-10 sm:w-10" on:click={() => showMusicSelector = false}>
            <svg class="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </Button>
        </div>
        <div class="flex-1 overflow-y-auto space-y-2 -mr-2 pr-2">
          {#each musicSources as source}
            <button
              class="w-full rounded-lg border border-zinc-800 p-2.5 sm:p-3 text-left transition-colors hover:bg-accent hover:border-zinc-700 {selectedMusicSource?.id === source.id ? 'border-primary bg-accent' : ''}"
              on:click={() => handleMusicSelectFromModal(source)}
              type="button"
            >
              <div class="flex gap-2.5 sm:gap-3">
                {#if source.thumbnail}
                  <img src={source.thumbnail} alt={source.name} class="w-14 h-14 sm:w-16 sm:h-16 rounded object-cover flex-shrink-0" />
                {/if}
                <div class="flex-1 min-w-0">
                  <p class="font-medium text-xs sm:text-sm line-clamp-2 mb-1">{source.name}</p>
                  <p class="text-[10px] sm:text-xs text-muted-foreground uppercase">{source.source_type}</p>
                </div>
              </div>
            </button>
          {/each}
        </div>
      </div>
    </Sheet>

    <Sheet bind:open={showStationSelector} onOpenChange={(open) => showStationSelector = open}>
      <div class="flex flex-col h-full">
        <div class="flex items-center justify-between mb-4 sm:mb-6">
          <h2 class="text-base sm:text-lg font-semibold">Select ATC Station</h2>
          <Button variant="ghost" size="icon" class="h-8 w-8 sm:h-10 sm:w-10" on:click={() => showStationSelector = false}>
            <svg class="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </Button>
        </div>
        <div class="flex-1 overflow-y-auto space-y-2 -mr-2 pr-2">
          {#each atcStations as station}
            <button
              class="w-full rounded-lg border border-zinc-800 p-3 sm:p-4 text-left transition-colors hover:bg-accent hover:border-zinc-700 {selectedAtcStation?.id === station.id ? 'border-primary bg-accent' : ''}"
              on:click={() => handleStationSelectFromModal(station)}
              type="button"
            >
              <div class="space-y-1">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-base sm:text-lg font-bold">{station.airport_code}</span>
                  <span class="text-[10px] sm:text-xs text-muted-foreground tabular-nums">{station.frequency} MHz</span>
                </div>
                <p class="text-xs sm:text-sm text-muted-foreground">{station.name}</p>
                <p class="text-[10px] sm:text-xs text-muted-foreground">{station.description}</p>
              </div>
            </button>
          {/each}
        </div>
      </div>
    </Sheet>

    <!-- Floating Action Button for Volume (Mobile Only) -->
    {#if isPlaying}
      <div class="md:hidden fixed bottom-6 right-6 z-40">
        {#if showVolumeControls}
          <div
            class="mb-3 w-72 sm:w-80 p-4 sm:p-5 rounded-xl border border-zinc-800 bg-card shadow-2xl space-y-4"
            transition:slide={{ duration: 200 }}
          >
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-semibold">Volume Controls</h3>
              <button
                class="text-muted-foreground hover:text-foreground transition-colors"
                on:click={() => showVolumeControls = false}
                type="button"
                aria-label="Close volume controls"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <svg class="w-4 h-4 text-muted-foreground" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}><!-- Icon from Pixel Icon by HackerNoon - https://creativecommons.org/licenses/by/4.0/ --><path fill="currentColor" d="M21 1v1h-3v1h-3v1h-4v1H8v1H6v10H3v1H2v1H1v3h1v1h1v1h4v-1h1v-1h1V11h2v-1h4V9h3V8h2v5h-3v1h-1v1h-1v3h1v1h1v1h4v-1h1v-1h1V1zM3 21v-3h4v3zM18 6v1h-3v1h-4v1H8V7h3V6h4V5h3V4h3v2zm-1 12v-3h4v3z"/></svg>
                  <span class="text-xs font-medium">Music</span>
                </div>
                <span class="text-xs text-muted-foreground tabular-nums">{Math.round(musicVolume[0] * 100)}%</span>
              </div>
              <Slider
                bind:value={musicVolume}
                onValueChange={handleMusicVolumeChange}
                min={0}
                max={1}
                step={0.01}
                class="touch-manipulation"
              />
            </div>

            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <!-- <Radio class="w-4 h-4 text-muted-foreground" /> -->
                  <svg class="w-4 h-4 text-muted-foreground" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}><!-- Icon from Pixelarticons by Gerrit Halfmann - https://github.com/halfmage/pixelarticons/blob/master/LICENSE --><path fill="currentColor" d="M19 2h2v2h-2zm2 14V4h2v12zm0 0v2h-2v-2zM1 4h2v12H1zm2 12h2v2H3zM3 4h2V2H3zm2 2h2v8H5zm2 8h2v2H7zm0-8h2V4H7zm10 0h2v8h-2zm0 0h-2V4h2zm0 8v2h-2v-2zm-6-7h4v6h-2v9h-2v-9H9V7zm0 4h2V9h-2z"/></svg>
                  <span class="text-xs font-medium">ATC Radio</span>
                </div>
                <span class="text-xs text-muted-foreground tabular-nums">{Math.round(atcVolume[0] * 100)}%</span>
              </div>
              <Slider
                bind:value={atcVolume}
                onValueChange={handleAtcVolumeChange}
                min={0}
                max={1}
                step={0.01}
                class="touch-manipulation"
              />
            </div>
          </div>
        {/if}

        <button
          class="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-primary text-primary-foreground shadow-2xl hover:scale-105 transition-all active:scale-95 flex items-center justify-center ml-auto"
          on:click={() => showVolumeControls = !showVolumeControls}
          type="button"
          aria-label="Toggle volume controls"
        >
          <!-- <Volume2 class="w-6 h-6 sm:w-7 sm:h-7" /> -->
          <svg class="w-6 h-6 sm:w-7 sm:h-7" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" {...$$props}><!-- Icon from Pixel Icon by HackerNoon - https://creativecommons.org/licenses/by/4.0/ --><path fill="currentColor" d="M14 2v20h-3v-1h-1v-1H9v-1H8v-1H7v-1H6v-1H1V8h5V7h1V6h1V5h1V4h1V3h1V2zm3 13v-1h-1v-1h1v-2h-1v-1h1V9h1v1h1v4h-1v1z"/><path fill="currentColor" d="M23 10v4h-1v2h-1v1h-1v1h-1v-1h-1v-1h1v-1h1v-1h1v-4h-1V9h-1V8h-1V7h1V6h1v1h1v1h1v2z"/></svg>
        </button>
      </div>
    {/if}
  {/if}

  <!-- Footer Attribution -->
  <footer class="fixed bottom-0 left-0 right-0 py-2.5 px-4 text-center bg-black/40 backdrop-blur-sm border-t border-zinc-800/50">
    <p class="text-xs text-muted-foreground">
      ATC audio provided by <a href="https://www.liveatc.net" target="_blank" rel="noopener noreferrer" class="text-primary hover:underline font-medium">LiveATC.net</a>
      · For personal, non-commercial use only
    </p>
  </footer>
</main>

