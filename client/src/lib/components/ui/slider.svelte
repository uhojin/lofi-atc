<script>
  import { cn } from '$lib/utils.js';

  let className = '';
  export { className as class };
  export let value = [0.5];
  export let min = 0;
  export let max = 1;
  export let step = 0.01;
  export let onValueChange = undefined;

  function handleInput(e) {
    const newValue = [parseFloat(e.target.value)];
    value = newValue;
    if (onValueChange) {
      onValueChange(newValue);
    }
  }
</script>

<span class={cn('relative flex w-full touch-none select-none items-center', className)} {...$$restProps}>
  <span class="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary">
    <span
      class="absolute h-full bg-primary"
      style="width: {((value[0] - min) / (max - min)) * 100}%"
    />
  </span>
  <input
    type="range"
    {min}
    {max}
    {step}
    value={value[0]}
    on:input={handleInput}
    class="absolute inset-0 w-full cursor-pointer opacity-0"
  />
  <span
    class="block h-5 w-5 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 pointer-events-none"
    style="position: absolute; left: calc({((value[0] - min) / (max - min)) * 100}% - 10px)"
  />
</span>
