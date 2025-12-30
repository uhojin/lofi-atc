<script>
  export let sources = [];
  export let selectedSource = null;
  export let onSelect;

  function handleSelect(source) {
    selectedSource = source;
    if (onSelect) {
      onSelect(source);
    }
  }
</script>

<div class="music-selector">
  <h3 class="section-title">Music Sources</h3>
  <div class="source-grid">
    {#each sources as source}
      <button
        class="source-button"
        class:active={selectedSource?.id === source.id}
        on:click={() => handleSelect(source)}
      >
        {#if source.thumbnail}
          <img src={source.thumbnail} alt={source.name} class="thumbnail" />
        {/if}
        <div class="source-info">
          <div class="source-name">{source.name}</div>
          <div class="source-type">{source.source_type.toUpperCase()}</div>
        </div>
      </button>
    {/each}
  </div>
</div>

<style>
  .music-selector {
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

  .source-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1rem;
  }

  .source-button {
    background: #0a0a0a;
    border: 2px solid #00ff00;
    padding: 0;
    cursor: pointer;
    transition: all 0.3s ease;
    overflow: hidden;
  }

  .source-button:hover {
    box-shadow: 0 0 15px rgba(0, 255, 0, 0.5);
  }

  .source-button.active {
    border-color: #00ff00;
    box-shadow: 0 0 20px rgba(0, 255, 0, 0.8);
  }

  .thumbnail {
    width: 100%;
    height: 140px;
    object-fit: cover;
    display: block;
    filter: grayscale(80%);
    transition: filter 0.3s;
  }

  .source-button:hover .thumbnail {
    filter: grayscale(20%);
  }

  .source-button.active .thumbnail {
    filter: grayscale(0%);
  }

  .source-info {
    padding: 0.75rem;
    background: #0a0a0a;
  }

  .source-name {
    color: #00ff00;
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
    font-family: monospace;
  }

  .source-type {
    color: #00ff00;
    font-size: 0.7rem;
    opacity: 0.6;
    font-family: monospace;
  }
</style>
