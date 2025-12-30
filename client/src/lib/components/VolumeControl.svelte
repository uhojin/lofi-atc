<script>
  export let label;
  export let value = 0.5;
  export let onChange;

  function handleChange(event) {
    const newValue = parseFloat(event.target.value);
    if (onChange) {
      onChange(newValue);
    }
  }
</script>

<div class="volume-control">
  <label>
    <span class="label-text">{label}</span>
    <input
      type="range"
      min="0"
      max="1"
      step="0.01"
      value={value}
      on:input={handleChange}
      class="slider"
    />
    <span class="value-display">{Math.round(value * 100)}%</span>
  </label>
</div>

<style>
  .volume-control {
    margin: 1rem 0;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .label-text {
    font-size: 0.9rem;
    font-weight: 500;
    color: #00ff00;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .slider {
    width: 100%;
    height: 8px;
    background: #1a1a1a;
    border: 1px solid #00ff00;
    outline: none;
    opacity: 0.8;
    transition: opacity 0.2s;
    appearance: none;
  }

  .slider:hover {
    opacity: 1;
  }

  .slider::-webkit-slider-thumb {
    appearance: none;
    width: 20px;
    height: 20px;
    background: #00ff00;
    cursor: pointer;
    border-radius: 50%;
  }

  .slider::-moz-range-thumb {
    width: 20px;
    height: 20px;
    background: #00ff00;
    cursor: pointer;
    border-radius: 50%;
    border: none;
  }

  .value-display {
    font-size: 0.85rem;
    color: #00ff00;
    text-align: right;
    font-family: monospace;
  }
</style>
