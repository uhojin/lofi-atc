<script>
  import { cn } from '$lib/utils.js';

  export let open = false;
  export let onOpenChange = undefined;

  function handleBackdropClick() {
    open = false;
    if (onOpenChange) {
      onOpenChange(false);
    }
  }

  function handleContentClick(e) {
    e.stopPropagation();
  }
</script>

{#if open}
  <div
    class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm"
    on:click={handleBackdropClick}
    role="button"
    tabindex="-1"
  >
    <div
      class={cn(
        'fixed inset-y-0 right-0 z-50 h-full w-full sm:w-3/4 gap-4 border-l border-zinc-800 bg-card p-4 sm:p-6 shadow-2xl transition ease-in-out sm:max-w-md',
        'animate-in slide-in-from-right duration-300'
      )}
      on:click={handleContentClick}
      role="dialog"
      tabindex="0"
    >
      <slot />
    </div>
  </div>
{/if}
