function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function serializeSvg(svgElement) {
  const cloned = svgElement.cloneNode(true);
  cloned.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  cloned.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");
  const source = new XMLSerializer().serializeToString(cloned);
  return source.startsWith("<?xml") ? source : `<?xml version="1.0" standalone="no"?>\n${source}`;
}

export function exportSvg(svgElement, filename = "chart.svg") {
  if (!svgElement) {
    return;
  }
  const source = serializeSvg(svgElement);
  downloadBlob(new Blob([source], { type: "image/svg+xml;charset=utf-8" }), filename);
}

export async function exportSvgAsPng(svgElement, filename = "chart.png") {
  if (!svgElement) {
    return;
  }
  const source = serializeSvg(svgElement);
  const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const image = new Image();
  image.decoding = "async";

  await new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = reject;
    image.src = url;
  });

  const viewBox = svgElement.viewBox.baseVal;
  const width = Math.max(1, viewBox?.width || svgElement.clientWidth || 1200);
  const height = Math.max(1, viewBox?.height || svgElement.clientHeight || 700);
  const canvas = document.createElement("canvas");
  canvas.width = width * 2;
  canvas.height = height * 2;
  const context = canvas.getContext("2d");
  context.scale(2, 2);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);
  context.drawImage(image, 0, 0, width, height);

  await new Promise((resolve) =>
    canvas.toBlob((pngBlob) => {
      if (pngBlob) {
        downloadBlob(pngBlob, filename);
      }
      resolve();
    }, "image/png")
  );
  URL.revokeObjectURL(url);
}
