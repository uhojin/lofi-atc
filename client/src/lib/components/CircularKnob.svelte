<script>
  export let label;
  export let value = 0.5;
  export let onChange;

  let isDragging = false;
  let knobElement;

  function handleMouseDown(event) {
    isDragging = true;
    updateValue(event);
  }

  function handleMouseMove(event) {
    if (isDragging) {
      updateValue(event);
    }
  }

  function handleMouseUp() {
    isDragging = false;
  }

  function updateValue(event) {
    if (!knobElement) return;

    const rect = knobElement.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const deltaX = event.clientX - centerX;
    const deltaY = event.clientY - centerY;

    let angle = Math.atan2(deltaY, deltaX) * (180 / Math.PI);
    angle = angle + 90;
    if (angle < 0) angle += 360;

    // Map 0-270 degrees to 0-1 (leaving a gap at bottom)
    const minAngle = 135;
    const maxAngle = 405;

    if (angle < minAngle) angle += 360;
    if (angle < minAngle) angle = minAngle;
    if (angle > maxAngle) angle = maxAngle;

    const normalizedAngle = (angle - minAngle) / (maxAngle - minAngle);
    const newValue = Math.max(0, Math.min(1, normalizedAngle));

    if (onChange) {
      onChange(newValue);
    }
  }

  $: rotation = 135 + (value * 270);
</script>

<svelte:window
  on:mousemove={handleMouseMove}
  on:mouseup={handleMouseUp}
/>

<div class="knob-container">
  <div
    class="knob"
    bind:this={knobElement}
    on:mousedown={handleMouseDown}
    role="slider"
    aria-valuemin="0"
    aria-valuemax="100"
    aria-valuenow={Math.round(value * 100)}
    aria-label={label}
    tabindex="0"
  >
    <div class="knob-track"></div>
    <div class="knob-fill" style="--rotation: {rotation}deg"></div>
    <div class="knob-handle" style="transform: rotate({rotation}deg)">
      <div class="handle-dot"></div>
    </div>
  </div>
  <div class="label">{label}</div>
</div>

<style>
  .knob-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
  }

  .knob {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: #ffffff;
    border: 3px solid #333;
    position: relative;
    cursor: pointer;
    user-select: none;
  }

  .knob-track {
    position: absolute;
    inset: 8px;
    border-radius: 50%;
    background: #e0e0e0;
  }

  .knob-fill {
    position: absolute;
    inset: 8px;
    border-radius: 50%;
    background: conic-gradient(
      from 135deg,
      #666 0deg,
      #666 var(--rotation),
      transparent var(--rotation)
    );
  }

  .knob-handle {
    position: absolute;
    width: 100%;
    height: 100%;
    transition: transform 0.05s ease-out;
  }

  .handle-dot {
    position: absolute;
    top: 12px;
    left: 50%;
    transform: translateX(-50%);
    width: 8px;
    height: 8px;
    background: #333;
    border-radius: 50%;
  }

  .label {
    font-size: 1rem;
    font-weight: 600;
    color: #000;
    text-align: center;
  }
</style>
