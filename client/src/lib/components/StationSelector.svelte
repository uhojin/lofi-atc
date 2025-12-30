<script>
  export let stations = [];
  export let selectedStation = null;
  export let onSelect;

  function handleSelect(station) {
    selectedStation = station;
    if (onSelect) {
      onSelect(station);
    }
  }
</script>

<div class="station-selector">
  <h3 class="section-title">ATC Stations</h3>
  <div class="station-grid">
    {#each stations as station}
      <button
        class="station-button"
        class:active={selectedStation?.id === station.id}
        on:click={() => handleSelect(station)}
      >
        <div class="airport-code">{station.airport_code}</div>
        <div class="station-name">{station.name}</div>
        <div class="frequency">{station.frequency} MHz</div>
      </button>
    {/each}
  </div>
</div>

<style>
  .station-selector {
    margin: 1.5rem 0;
  }

  .section-title {
    color: #00ff00;
    font-size: 1.2rem;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 600;
  }

  .station-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
  }

  .station-button {
    background: #0a0a0a;
    border: 2px solid #00ff00;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    color: #00ff00;
    font-family: monospace;
  }

  .station-button:hover {
    background: #1a1a1a;
    box-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
  }

  .station-button.active {
    background: #00ff00;
    color: #000;
    font-weight: bold;
  }

  .airport-code {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
  }

  .station-name {
    font-size: 0.85rem;
    margin-bottom: 0.25rem;
  }

  .frequency {
    font-size: 0.75rem;
    opacity: 0.8;
  }
</style>
