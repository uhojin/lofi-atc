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
    margin: 0;
  }

  .section-title {
    color: #333;
    font-size: 1.2rem;
    margin-bottom: 1rem;
    font-weight: 600;
  }

  .station-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
  }

  .station-button {
    background: #ffffff;
    border: 2px solid #333;
    padding: 1.25rem;
    cursor: pointer;
    transition: all 0.2s ease;
    color: #333;
    font-family: inherit;
  }

  .station-button:hover {
    background: #f8f8f8;
    border-color: #000;
  }

  .station-button.active {
    background: #333;
    color: #ffffff;
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
    opacity: 0.7;
  }
</style>
