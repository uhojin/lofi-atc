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
    margin: 0;
  }

  .section-title {
    color: #333;
    font-size: 1.2rem;
    margin-bottom: 1rem;
    font-weight: 600;
  }

  .source-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
  }

  .source-button {
    background: #ffffff;
    border: 2px solid #333;
    padding: 0;
    cursor: pointer;
    transition: all 0.2s ease;
    overflow: hidden;
  }

  .source-button:hover {
    border-color: #000;
  }

  .source-button.active {
    border-color: #000;
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
  }

  .thumbnail {
    width: 100%;
    height: 140px;
    object-fit: cover;
    display: block;
    transition: opacity 0.2s;
    opacity: 0.9;
  }

  .source-button:hover .thumbnail {
    opacity: 1;
  }

  .source-button.active .thumbnail {
    opacity: 1;
  }

  .source-info {
    padding: 0.75rem;
    background: #ffffff;
  }

  .source-name {
    color: #333;
    font-size: 0.85rem;
    margin-bottom: 0.25rem;
    font-family: inherit;
  }

  .source-type {
    color: #666;
    font-size: 0.7rem;
    font-family: inherit;
  }
</style>
