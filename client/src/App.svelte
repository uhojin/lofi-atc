<script>
  import { onMount, onDestroy } from "svelte";
  import { AudioEngine } from "./lib/audio/audioEngine.js";
  import {
    getAtcStations,
    getMusicSources,
    getProxyUrl,
    getMusicStreamUrl,
  } from "./lib/api.js";
  import Card from "./lib/components/ui/card.svelte";
  import Button from "./lib/components/ui/button.svelte";
  import Slider from "./lib/components/ui/slider.svelte";
  import Sheet from "./lib/components/ui/sheet.svelte";
  import {
    Music,
    Radio,
    Volume2,
    Disc3,
    Play,
    Pause,
    ChevronDown,
    ChevronUp,
    ChevronLeft,
    ChevronRight,
  } from "lucide-svelte";

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
  let musicTitleRef;
  let shouldScrollTitle = false;
  let atcNameRef;
  let shouldScrollAtcName = false;
  let modalStationNameRefs = {};
  let shouldScrollModalStationName = {};
  let modalStationDescRefs = {};
  let shouldScrollModalStationDesc = {};

  // Track which station index is displayed per airport group
  let airportStationIndex = {};

  // Group stations by airport_code
  $: groupedStations = atcStations.reduce((acc, station) => {
    const code = station.airport_code;
    if (!acc[code]) acc[code] = [];
    acc[code].push(station);
    return acc;
  }, {});

  // Sorted airport codes for consistent ordering
  $: airportCodes = Object.keys(groupedStations).sort();

  // Initialize index state when stations load
  $: if (
    atcStations.length > 0 &&
    Object.keys(airportStationIndex).length === 0
  ) {
    airportStationIndex = Object.fromEntries(
      Object.keys(groupedStations).map((code) => [code, 0]),
    );
  }

  function setStationIndex(airportCode, index) {
    // Reset scroll state before changing station
    shouldScrollModalStationName = {
      ...shouldScrollModalStationName,
      [airportCode]: false,
    };
    shouldScrollModalStationDesc = {
      ...shouldScrollModalStationDesc,
      [airportCode]: false,
    };
    airportStationIndex = { ...airportStationIndex, [airportCode]: index };
  }

  function cycleStationLeft(airportCode) {
    const stations = groupedStations[airportCode];
    if (!stations || stations.length <= 1) return;
    const newIndex =
      (airportStationIndex[airportCode] - 1 + stations.length) %
      stations.length;
    setStationIndex(airportCode, newIndex);
  }

  function cycleStationRight(airportCode) {
    const stations = groupedStations[airportCode];
    if (!stations || stations.length <= 1) return;
    const newIndex = (airportStationIndex[airportCode] + 1) % stations.length;
    setStationIndex(airportCode, newIndex);
  }

  function checkTitleOverflow() {
    if (musicTitleRef) {
      const scrollWidth = musicTitleRef.scrollWidth;
      const clientWidth = musicTitleRef.clientWidth;
      shouldScrollTitle = scrollWidth > clientWidth;
    }
  }

  function checkAtcNameOverflow() {
    if (atcNameRef) {
      shouldScrollAtcName = atcNameRef.scrollWidth > atcNameRef.clientWidth;
    }
  }

  function checkModalStationNameOverflow(airportCode) {
    const ref = modalStationNameRefs[airportCode];
    if (ref) {
      shouldScrollModalStationName = {
        ...shouldScrollModalStationName,
        [airportCode]: ref.scrollWidth > ref.clientWidth,
      };
    }
  }

  function checkModalStationDescOverflow(airportCode) {
    const ref = modalStationDescRefs[airportCode];
    if (ref) {
      shouldScrollModalStationDesc = {
        ...shouldScrollModalStationDesc,
        [airportCode]: ref.scrollWidth > ref.clientWidth,
      };
    }
  }

  function checkAllModalStationNames() {
    Object.keys(modalStationNameRefs).forEach(checkModalStationNameOverflow);
    Object.keys(modalStationDescRefs).forEach(checkModalStationDescOverflow);
  }

  function handleResize() {
    checkTitleOverflow();
    checkAtcNameOverflow();
    checkAllModalStationNames();
  }

  // Reactive statement to check overflow when music source changes
  $: if (selectedMusicSource && musicTitleRef) {
    setTimeout(checkTitleOverflow, 100);
  }

  // Reactive statement to check overflow when ATC station changes
  $: if (selectedAtcStation && atcNameRef) {
    setTimeout(checkAtcNameOverflow, 100);
  }

  // Reactive statement to re-check modal station names when modal opens or station index changes
  $: if (showStationSelector && Object.keys(airportStationIndex).length > 0) {
    setTimeout(checkAllModalStationNames, 100);
  }

  function handleKeyPress(e) {
    // Check if spacebar is pressed
    if (e.code === "Space" || e.key === " ") {
      // Prevent default scrolling behavior
      e.preventDefault();
      // Toggle play/pause
      togglePlayPause();
    }
  }

  onMount(async () => {
    try {
      audioEngine = new AudioEngine();

      const [stations, sources] = await Promise.all([
        getAtcStations(),
        getMusicSources(),
      ]);

      atcStations = stations;
      musicSources = sources;
      loading = false;
    } catch (err) {
      console.error("Failed to load data:", err);
      error =
        "Failed to connect to server. Make sure the backend is running on port 3000.";
      loading = false;
    }

    // Add resize listener to re-check title overflow
    window.addEventListener("resize", handleResize);
    // Add spacebar listener for play/pause
    window.addEventListener("keydown", handleKeyPress);
  });

  onDestroy(() => {
    if (audioEngine) {
      audioEngine.destroy();
    }
    window.removeEventListener("resize", handleResize);
    window.removeEventListener("keydown", handleKeyPress);
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
      console.error("Failed to play ATC station:", err);
      error = "Failed to play ATC stream. The station might be offline.";
    }
  }

  async function handleMusicSourceSelect(source) {
    try {
      if (!isPlaying) {
        await audioEngine.init();
        isPlaying = true;
      }

      error = "Starting music stream...";

      const streamUrl = getMusicStreamUrl(source.id);
      console.log("Playing music stream:", source.name);

      if (selectedMusicSource) {
        await audioEngine.switchMusicSource(streamUrl);
      } else {
        await audioEngine.playMusic(streamUrl);
      }

      selectedMusicSource = source;
      error = null;

      // Check title overflow after selection
      setTimeout(checkTitleOverflow, 100);
    } catch (err) {
      console.error("Failed to play music source:", err);
      error = "Failed to play music stream. The source might be unavailable.";
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

  async function handleStationSelectFromModal(station) {
    await handleAtcStationSelect(station);
    // Only close modal on success (error will be null, selectedAtcStation will be set)
    if (!error) {
      showStationSelector = false;
    }
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
      console.error("Failed to toggle playback:", err);
      error = "Failed to toggle playback";
    }
  }
</script>

<main
  class="min-h-screen flex items-center justify-center p-3 sm:p-4 md:p-6 bg-gradient-to-br from-black via-zinc-950 to-zinc-900"
>
  {#if loading}
    <div class="flex flex-col items-center gap-4">
      <svg
        class="w-10 h-10 sm:w-12 sm:h-12 motion-safe:animate-spin text-primary"
        xmlns="http://www.w3.org/2000/svg"
        width="1em"
        height="1em"
        viewBox="0 0 24 24"
        {...$$props}
        ><!-- Icon from Pixel Icon by HackerNoon - https://creativecommons.org/licenses/by/4.0/ --><path
          fill="currentColor"
          d="M11 20h-1v2H9v1H5v-1H4v-6h1v-1h1v3h2v-1h2v-1h2v-1h2v2h-1v1h-2z"
        /><path
          fill="currentColor"
          d="M22 9V7h-1V5h-1V4h-1V3h-2V2h-2V1H9v1H7v1H5v1H4v1H3v2H2v2H1v6h1v1h1v-1h1v-1h3v2h2v-1h2v-1h-1v-1H8v-1h3v1h2v1h2v4h-1v1h-2v2h-1v2h4v-1h2v-1h2v-1h1v-1h1v-2h1v-2h1V9zm-7-2h3v1h1v2h-1V9h-1V8h-2zm-1 2h2v2h-2zm-4 1H8V8h2zm1-2V7h-1V6H8v1H6V6h1V5h4v1h1v1h1v1z"
        /></svg
      >
      <p class="text-sm text-muted-foreground">Loading...</p>
    </div>
  {:else}
    <div class="w-full max-w-sm md:max-w-md lg:max-w-lg">
      <Card
        class="p-4 sm:p-6 md:p-8 space-y-4 sm:space-y-5 md:space-y-6 border-zinc-800 shadow-2xl"
      >
        <div class="space-y-1 sm:space-y-2 text-center">
          <h1 class="text-xl sm:text-2xl md:text-3xl font-bold tracking-tight">
            Lofi ATC Radio
          </h1>
          <p class="text-xs sm:text-sm text-muted-foreground">
            Mix lofi beats with live air traffic control
          </p>
        </div>

        <!-- Dual Card Container -->
        <div
          class="relative grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5 md:gap-6"
        >
          <!-- Music Source Card -->
          <button
            class="group relative aspect-[2/1] md:aspect-square overflow-hidden rounded-lg bg-muted border border-zinc-800 hover:border-zinc-700 transition-all duration-300 cursor-pointer {selectedMusicSource
              ? 'ring-2 ring-primary/20'
              : ''}"
            on:click={toggleMusicSelector}
            type="button"
          >
            {#if selectedMusicSource?.thumbnail}
              <img
                src={selectedMusicSource.thumbnail}
                alt={selectedMusicSource.name}
                class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105 {isPaused
                  ? 'opacity-60'
                  : ''}"
              />
              <div
                class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              ></div>

              <!-- Music Icon Overlay on Hover -->
              <div
                class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              >
                <svg
                  class="w-12 h-12 sm:w-16 sm:h-16 text-white drop-shadow-lg"
                  xmlns="http://www.w3.org/2000/svg"
                  width="1em"
                  height="1em"
                  viewBox="0 0 24 24"
                >
                  <path
                    fill="currentColor"
                    d="M23 1v17h-1v1h-1v1h-4v-1h-1v-1h-1v-3h1v-1h1v-1h3V8h-2v1h-3v1h-4v1H9v10H8v1H7v1H3v-1H2v-1H1v-3h1v-1h1v-1h3V6h2V5h3V4h4V3h3V2h3V1z"
                  />
                </svg>
              </div>

              <!-- Playing Indicator -->
              {#if isPlaying && selectedMusicSource}
                <div
                  class="absolute top-2 right-2 sm:top-3 sm:right-3 flex items-center gap-1.5 px-2 py-1 rounded-full bg-black/60 backdrop-blur-sm border border-white/20"
                >
                  <div
                    class="w-1.5 h-1.5 bg-green-500 rounded-full {isPaused
                      ? 'bg-orange-400'
                      : 'animate-pulse'}"
                  ></div>
                  <span class="text-[10px] text-white font-medium uppercase"
                    >{isPaused ? "Paused" : "Playing"}</span
                  >
                </div>
              {/if}

              <!-- Music Info Overlay -->
              <div
                class="absolute bottom-0 left-0 right-0 p-3 sm:p-4 bg-gradient-to-t from-black/90 to-transparent overflow-hidden"
              >
                <h3
                  bind:this={musicTitleRef}
                  class="font-semibold text-sm sm:text-base text-white whitespace-nowrap overflow-hidden"
                >
                  {#if shouldScrollTitle}
                    <span class="inline-flex animate-marquee">
                      <span class="inline-block px-4"
                        >{selectedMusicSource.name}</span
                      >
                      <span class="inline-block px-4"
                        >{selectedMusicSource.name}</span
                      >
                    </span>
                  {:else}
                    <span class="inline-block">{selectedMusicSource.name}</span>
                  {/if}
                </h3>
                <p class="text-xs text-white/70 uppercase mt-0.5">
                  {selectedMusicSource.source_type}
                </p>
              </div>
            {:else}
              <!-- Empty State -->
              <div
                class="w-full h-full flex flex-col items-center justify-center text-muted-foreground group-hover:text-foreground transition-colors bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900"
              >
                <svg
                  class="w-12 h-12 sm:w-16 sm:h-16 mb-2 sm:mb-3"
                  xmlns="http://www.w3.org/2000/svg"
                  width="1em"
                  height="1em"
                  viewBox="0 0 24 24"
                >
                  <path
                    fill="currentColor"
                    d="M21 1v1h-3v1h-3v1h-4v1H8v1H6v10H3v1H2v1H1v3h1v1h1v1h4v-1h1v-1h1V11h2v-1h4V9h3V8h2v5h-3v1h-1v1h-1v3h1v1h1v1h4v-1h1v-1h1V1zM3 21v-3h4v3zM18 6v1h-3v1h-4v1H8V7h3V6h4V5h3V4h3v2zm-1 12v-3h4v3z"
                  />
                </svg>
                <p class="text-xs sm:text-sm font-medium">Select Music</p>
              </div>
            {/if}
          </button>

          <!-- ATC Station Card -->
          <button
            class="group relative aspect-2/1 md:aspect-square overflow-hidden rounded-lg bg-muted border border-zinc-800 hover:border-zinc-700 transition-all duration-300 cursor-pointer {selectedAtcStation
              ? 'ring-2 ring-primary/20'
              : ''}"
            on:click={toggleStationSelector}
            type="button"
          >
            {#if selectedAtcStation}
              <!-- ATC Visual Background -->
              <div
                class="absolute inset-0 bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900"
              >
                <!-- Decorative Grid Pattern -->
                <div
                  class="absolute inset-0 opacity-10"
                  style="background-image: repeating-linear-gradient(0deg, transparent, transparent 35px, #fbbf24 35px, #fbbf24 36px), repeating-linear-gradient(90deg, transparent, transparent 35px, #fbbf24 35px, #fbbf24 36px);"
                ></div>
              </div>

              <!-- ATC Icon Centered -->
              <div
                class="absolute inset-0 flex items-center justify-center opacity-20 group-hover:opacity-30 transition-opacity"
              >
                <svg
                  class="w-12 h-12 sm:w-16 sm:h-16"
                  xmlns="http://www.w3.org/2000/svg"
                  width="1em"
                  height="1em"
                  viewBox="0 0 24 24"
                >
                  <path
                    fill="currentColor"
                    d="M19 2h2v2h-2zm2 14V4h2v12zm0 0v2h-2v-2zM1 4h2v12H1zm2 12h2v2H3zM3 4h2V2H3zm2 2h2v8H5zm2 8h2v2H7zm0-8h2V4H7zm10 0h2v8h-2zm0 0h-2V4h2zm0 8v2h-2v-2zm-6-7h4v6h-2v9h-2v-9H9V7zm0 4h2V9h-2z"
                  />
                </svg>
              </div>

              <!-- Playing Indicator -->
              {#if isPlaying && selectedAtcStation}
                <div
                  class="absolute top-2 right-2 sm:top-3 sm:right-3 flex items-center gap-1.5 px-2 py-1 rounded-full bg-black/60 backdrop-blur-sm border border-white/20"
                >
                  <div
                    class="w-1.5 h-1.5 bg-green-500 rounded-full {isPaused
                      ? 'bg-orange-400'
                      : 'animate-pulse'}"
                  ></div>
                  <span class="text-[10px] text-white font-medium uppercase"
                    >{isPaused ? "Paused" : "Live"}</span
                  >
                </div>
              {/if}

              <!-- ATC Info Overlay -->
              <div
                class="absolute bottom-0 left-0 right-0 p-3 sm:p-4 bg-gradient-to-t from-black/90 to-transparent"
              >
                <div class="flex items-baseline justify-between gap-2">
                  <h3 class="text-xl sm:text-2xl font-bold text-white">
                    {selectedAtcStation.airport_code}
                  </h3>
                  <span
                    class="text-[10px] sm:text-xs text-white/70 tabular-nums"
                    >{selectedAtcStation.frequency} MHz</span
                  >
                </div>
                <p
                  bind:this={atcNameRef}
                  class="text-xs sm:text-sm text-white/90 whitespace-nowrap overflow-hidden mt-1"
                >
                  {#if shouldScrollAtcName}
                    <span class="inline-flex animate-marquee">
                      <span class="inline-block px-4"
                        >{selectedAtcStation.name}</span
                      >
                      <span class="inline-block px-4"
                        >{selectedAtcStation.name}</span
                      >
                    </span>
                  {:else}
                    <span class="inline-block">{selectedAtcStation.name}</span>
                  {/if}
                </p>
              </div>

              <!-- Hover Overlay -->
              <div
                class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors"
              ></div>
            {:else}
              <!-- Empty State -->
              <div
                class="w-full h-full flex flex-col items-center justify-center text-muted-foreground group-hover:text-foreground transition-colors bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900"
              >
                <svg
                  class="w-12 h-12 sm:w-16 sm:h-16 mb-2 sm:mb-3"
                  xmlns="http://www.w3.org/2000/svg"
                  width="1em"
                  height="1em"
                  viewBox="0 0 24 24"
                >
                  <path
                    fill="currentColor"
                    d="M19 2h2v2h-2zm2 14V4h2v12zm0 0v2h-2v-2zM1 4h2v12H1zm2 12h2v2H3zM3 4h2V2H3zm2 2h2v8H5zm2 8h2v2H7zm0-8h2V4H7zm10 0h2v8h-2zm0 0h-2V4h2zm0 8v2h-2v-2zm-6-7h4v6h-2v9h-2v-9H9V7zm0 4h2V9h-2z"
                  />
                </svg>
                <p class="text-xs sm:text-sm font-medium">Select ATC Station</p>
              </div>
            {/if}
          </button>

          <!-- Central Play/Pause Button -->
          {#if isPlaying}
            <div
              class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10"
            >
              <button
                class="w-14 h-14 sm:w-16 sm:h-16 md:w-20 md:h-20 rounded-full bg-primary text-primary-foreground shadow-2xl hover:scale-105 transition-transform active:scale-95 flex items-center justify-center ring-4 ring-primary/30"
                on:click={togglePlayPause}
                type="button"
                aria-label={isPaused ? "Play" : "Pause"}
              >
                {#if isPaused}
                  <svg
                    class="w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8 ml-0.5"
                    fill="currentColor"
                    xmlns="http://www.w3.org/2000/svg"
                    width="1em"
                    height="1em"
                    viewBox="0 0 24 24"
                  >
                    <path
                      fill="currentColor"
                      d="M22 11v2h-1v1h-1v1h-2v1h-2v1h-1v1h-2v1h-2v1h-1v1H8v1H6v1H3v-1H2V2h1V1h3v1h2v1h2v1h1v1h2v1h2v1h1v1h2v1h2v1h1v1z"
                    />
                  </svg>
                {:else}
                  <svg
                    class="w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8"
                    xmlns="http://www.w3.org/2000/svg"
                    width="1em"
                    height="1em"
                    viewBox="0 0 24 24"
                  >
                    <path
                      fill="currentColor"
                      d="M23 2v20h-1v1h-7v-1h-1V2h1V1h7v1zM9 2h1v20H9v1H2v-1H1V2h1V1h7z"
                    />
                  </svg>
                {/if}
              </button>
            </div>
          {/if}
        </div>

        <!-- Inline Volume Controls -->
        {#if isPlaying}
          <div class="space-y-3 sm:space-y-4">
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <svg
                    class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-muted-foreground"
                    xmlns="http://www.w3.org/2000/svg"
                    width="1em"
                    height="1em"
                    viewBox="0 0 24 24"
                    {...$$props}
                    ><!-- Icon from Pixel Icon by HackerNoon - https://creativecommons.org/licenses/by/4.0/ --><path
                      fill="currentColor"
                      d="M21 1v1h-3v1h-3v1h-4v1H8v1H6v10H3v1H2v1H1v3h1v1h1v1h4v-1h1v-1h1V11h2v-1h4V9h3V8h2v5h-3v1h-1v1h-1v3h1v1h1v1h4v-1h1v-1h1V1zM3 21v-3h4v3zM18 6v1h-3v1h-4v1H8V7h3V6h4V5h3V4h3v2zm-1 12v-3h4v3z"
                    /></svg
                  >
                  <span class="text-xs sm:text-sm font-medium">Music</span>
                </div>
                <span class="text-xs text-muted-foreground tabular-nums"
                  >{Math.round(musicVolume[0] * 100)}%</span
                >
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
                  <svg
                    class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-muted-foreground"
                    xmlns="http://www.w3.org/2000/svg"
                    width="1em"
                    height="1em"
                    viewBox="0 0 24 24"
                    {...$$props}
                    ><!-- Icon from Pixelarticons by Gerrit Halfmann - https://github.com/halfmage/pixelarticons/blob/master/LICENSE --><path
                      fill="currentColor"
                      d="M19 2h2v2h-2zm2 14V4h2v12zm0 0v2h-2v-2zM1 4h2v12H1zm2 12h2v2H3zM3 4h2V2H3zm2 2h2v8H5zm2 8h2v2H7zm0-8h2V4H7zm10 0h2v8h-2zm0 0h-2V4h2zm0 8v2h-2v-2zm-6-7h4v6h-2v9h-2v-9H9V7zm0 4h2V9h-2z"
                    /></svg
                  >
                  <span class="text-xs sm:text-sm font-medium">ATC Radio</span>
                </div>
                <span class="text-xs text-muted-foreground tabular-nums"
                  >{Math.round(atcVolume[0] * 100)}%</span
                >
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

        {#if error}
          <div
            class="rounded-lg bg-destructive/10 border border-destructive/20 p-2.5 sm:p-3 text-xs sm:text-sm text-destructive"
          >
            {error}
          </div>
        {/if}
      </Card>
    </div>

    <Sheet
      bind:open={showMusicSelector}
      onOpenChange={(open) => (showMusicSelector = open)}
    >
      <div class="flex flex-col h-full">
        <div class="flex items-center justify-between mb-4 sm:mb-5 md:mb-6">
          <h2 class="text-xl sm:text-2xl md:text-3xl font-semibold">
            Select Music Source
          </h2>
          <Button
            variant="ghost"
            size="icon"
            class="h-10 w-10 sm:h-11 sm:w-11 md:h-12 md:w-12"
            on:click={() => (showMusicSelector = false)}
          >
            <svg
              class="w-5 h-5 sm:w-6 sm:h-6 md:w-7 md:h-7"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </Button>
        </div>
        <div
          class="flex-1 overflow-y-auto space-y-2.5 sm:space-y-3 md:space-y-3.5 -mr-2 pr-2"
        >
          {#each musicSources as source}
            <button
              class="w-full rounded-lg border border-zinc-800 p-3.5 sm:p-4 md:p-5 text-left transition-colors hover:bg-accent hover:border-zinc-700 {selectedMusicSource?.id ===
              source.id
                ? 'border-primary bg-accent'
                : ''}"
              on:click={() => handleMusicSelectFromModal(source)}
              type="button"
            >
              <div class="flex gap-3.5 sm:gap-4 md:gap-5">
                {#if source.thumbnail}
                  <img
                    src={source.thumbnail}
                    alt={source.name}
                    class="w-18 h-18 sm:w-20 sm:h-20 md:w-24 md:h-24 rounded object-cover flex-shrink-0"
                  />
                {/if}
                <div class="flex-1 min-w-0">
                  <p
                    class="font-medium text-base sm:text-lg md:text-xl line-clamp-2 mb-1.5"
                  >
                    {source.name}
                  </p>
                  <p
                    class="text-sm sm:text-base md:text-lg text-muted-foreground uppercase"
                  >
                    {source.source_type}
                  </p>
                </div>
              </div>
            </button>
          {/each}
        </div>
      </div>
    </Sheet>

    <Sheet
      bind:open={showStationSelector}
      onOpenChange={(open) => (showStationSelector = open)}
    >
      <div class="flex flex-col h-full">
        <div class="flex items-center justify-between mb-4 sm:mb-5 md:mb-6">
          <h2 class="text-xl sm:text-2xl md:text-3xl font-semibold">
            Select ATC Station
          </h2>
          <Button
            variant="ghost"
            size="icon"
            class="h-10 w-10 sm:h-11 sm:w-11 md:h-12 md:w-12"
            on:click={() => (showStationSelector = false)}
          >
            <svg
              class="w-5 h-5 sm:w-6 sm:h-6 md:w-7 md:h-7"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </Button>
        </div>
        {#if error}
          <div
            class="rounded-lg bg-destructive/10 border border-destructive/20 p-2.5 sm:p-3 text-xs sm:text-sm text-destructive mb-4"
          >
            {error}
          </div>
        {/if}
        <div
          class="flex-1 overflow-y-auto space-y-2.5 sm:space-y-3 md:space-y-3.5"
        >
          {#each airportCodes as airportCode}
            {@const stations = groupedStations[airportCode]}
            {@const currentIndex = airportStationIndex[airportCode] ?? 0}
            {@const currentStation = stations[currentIndex]}
            {@const hasMultiple = stations.length > 1}
            {@const isCurrentlyPlaying =
              isPlaying && selectedAtcStation?.id === currentStation.id}

            <div
              class="relative w-full rounded-lg border border-zinc-800 p-3.5 sm:p-4 md:p-5 transition-colors hover:border-zinc-700 {selectedAtcStation?.id ===
              currentStation.id
                ? 'border-primary bg-accent'
                : ''}"
            >
              <div class="flex items-center gap-2">
                <!-- Station Info (clickable) -->
                <button
                  class="flex-1 text-left min-w-0"
                  on:click={() => handleStationSelectFromModal(currentStation)}
                  type="button"
                >
                  <div class="space-y-1.5 sm:space-y-2 md:space-y-2.5">
                    <div class="flex items-center justify-between gap-2">
                      <div class="flex">
                        <span class="text-xl sm:text-2xl md:text-3xl font-bold"
                          >{currentStation.airport_code}
                        </span>

                        <!-- Now Playing Badge -->
                        {#if isCurrentlyPlaying}
                          <div
                            class="flex items-center gap-1.5 px-2 py-1 rounded-full"
                          >
                            <div
                              class="w-1.5 h-1.5 bg-green-500 rounded-full {isPaused
                                ? 'bg-orange-400'
                                : 'animate-pulse'}"
                            ></div>
                          </div>
                        {/if}
                      </div>

                      <span
                        class="text-sm sm:text-base md:text-lg text-muted-foreground tabular-nums"
                        >{currentStation.frequency} MHz</span
                      >
                    </div>
                    <p
                      bind:this={modalStationNameRefs[airportCode]}
                      class="text-base sm:text-lg md:text-xl text-muted-foreground whitespace-nowrap overflow-hidden"
                    >
                      {#if shouldScrollModalStationName[airportCode]}
                        <span class="inline-flex animate-marquee">
                          <span class="inline-block px-4"
                            >{currentStation.name}</span
                          >
                          <span class="inline-block px-4"
                            >{currentStation.name}</span
                          >
                        </span>
                      {:else}
                        <span class="inline-block">{currentStation.name}</span>
                      {/if}
                    </p>
                    <p
                      bind:this={modalStationDescRefs[airportCode]}
                      class="text-sm sm:text-base md:text-lg text-muted-foreground whitespace-nowrap overflow-hidden"
                    >
                      {#if shouldScrollModalStationDesc[airportCode]}
                        <span class="inline-flex animate-marquee">
                          <span class="inline-block px-4"
                            >{currentStation.description}</span
                          >
                          <span class="inline-block px-4"
                            >{currentStation.description}</span
                          >
                        </span>
                      {:else}
                        <span class="inline-block"
                          >{currentStation.description}</span
                        >
                      {/if}
                    </p>
                  </div>
                </button>
              </div>

              <!-- Dot Indicators -->
              {#if hasMultiple}
                <div
                  class="flex items-center justify-between gap-2 mt-3 pt-2 border-t border-zinc-800/50"
                >
                  <!-- Left Arrow -->
                  <button
                    class="flex-shrink-0 p-1.5 sm:p-2 rounded-md hover:bg-zinc-700/50 transition-colors text-muted-foreground hover:text-foreground"
                    on:click|stopPropagation={() =>
                      cycleStationLeft(airportCode)}
                    type="button"
                    aria-label="Previous station"
                  >
                    <ChevronLeft class="w-5 h-5 sm:w-6 sm:h-6" />
                  </button>

                  <div class="flex-1 flex items-center justify-center gap-4">
                    <div class="flex items-center gap-1.5">
                      {#each stations as _, i}
                        <button
                          class="w-2 h-2 rounded-full transition-colors {i ===
                          currentIndex
                            ? 'bg-primary'
                            : 'bg-zinc-600 hover:bg-zinc-500'}"
                          on:click|stopPropagation={() =>
                            setStationIndex(airportCode, i)}
                          type="button"
                          aria-label="Go to station {i + 1}"
                        ></button>
                      {/each}
                    </div>
                    <span class="text-xs text-muted-foreground tabular-nums"
                      >{currentIndex + 1}/{stations.length}</span
                    >
                  </div>

                  <!-- Right Arrow -->
                  <button
                    class="flex-shrink-0 p-1.5 sm:p-2 rounded-md hover:bg-zinc-700/50 transition-colors text-muted-foreground hover:text-foreground"
                    on:click|stopPropagation={() =>
                      cycleStationRight(airportCode)}
                    type="button"
                    aria-label="Next station"
                  >
                    <ChevronRight class="w-5 h-5 sm:w-6 sm:h-6" />
                  </button>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    </Sheet>
  {/if}

  <!-- Footer Attribution -->
  <footer
    class="fixed bottom-0 left-0 right-0 py-2.5 px-4 text-center bg-black/40 backdrop-blur-sm border-t border-zinc-800/50"
  >
    <p class="text-xs text-muted-foreground">
      ATC audio provided by <a
        href="https://www.liveatc.net"
        target="_blank"
        rel="noopener noreferrer"
        class="text-primary hover:underline font-medium">LiveATC.net</a
      >
      · For personal, non-commercial use only
    </p>
  </footer>
</main>

<style>
  @keyframes marquee {
    0% {
      transform: translateX(0%);
    }
    100% {
      transform: translateX(-50%);
    }
  }

  .animate-marquee {
    animation: marquee 15s linear infinite;
  }
</style>
