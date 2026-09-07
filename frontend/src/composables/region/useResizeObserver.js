import { onBeforeUnmount, onMounted } from "vue";

export function useResizeObserver(targetRef, callback) {
  let frameId = null;
  let observer = null;

  function trigger() {
    if (frameId !== null) {
      cancelAnimationFrame(frameId);
    }
    frameId = requestAnimationFrame(() => {
      frameId = null;
      callback();
    });
  }

  onMounted(() => {
    if (!targetRef.value || typeof ResizeObserver === "undefined") {
      window.addEventListener("resize", trigger);
      return;
    }
    observer = new ResizeObserver(() => trigger());
    observer.observe(targetRef.value);
    trigger();
  });

  onBeforeUnmount(() => {
    if (frameId !== null) {
      cancelAnimationFrame(frameId);
    }
    if (observer) {
      observer.disconnect();
    } else {
      window.removeEventListener("resize", trigger);
    }
  });

  return { trigger };
}
