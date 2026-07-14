const SVG_NS = "http://www.w3.org/2000/svg";

const evidenceStyles = Object.freeze({
  observed: { color: "#1f8a5b", dash: "0", label: "Observed" },
  modelled: { color: "#3b4ea0", dash: "3 5", label: "Modelled" },
  projected: { color: "#c98a17", dash: "10 6", label: "Projected" },
});

export function evidenceClass(type) {
  return `evidence-${evidenceStyles[type] ? type : "unknown"}`;
}

export function evidenceStyle(type) {
  return evidenceStyles[type] ?? { color: "#8a93a7", dash: "2 4", label: "Unknown" };
}

export function formatCompact(value, language = "en") {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  const abs = Math.abs(number);
  if (abs >= 1_000_000) {
    const rendered = (number / 1_000_000).toFixed(abs >= 10_000_000 ? 1 : 2).replace(/\.0+$/, "");
    return language === "pl" ? `${rendered.replace(".", ",")} mln` : `${rendered}M`;
  }
  if (abs >= 1_000) {
    const rendered = (number / 1_000).toFixed(abs >= 100_000 ? 0 : 1).replace(/\.0$/, "");
    return language === "pl" ? `${rendered.replace(".", ",")} tys.` : `${rendered}k`;
  }
  return new Intl.NumberFormat(language === "pl" ? "pl-PL" : "en-GB", { maximumFractionDigits: 2 }).format(number);
}

function scaleLinear(value, domainMin, domainMax, rangeMin, rangeMax) {
  if (domainMin === domainMax) return (rangeMin + rangeMax) / 2;
  return rangeMin + ((value - domainMin) / (domainMax - domainMin)) * (rangeMax - rangeMin);
}

export function linePath(points, { width, height, padding = 0 } = {}) {
  if (!points.length) return "";
  const xs = points.map((point) => Number(point.x));
  const ys = points.map((point) => Number(point.y));
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMin = Math.min(...ys, 0);
  const yMax = Math.max(...ys);
  return points.map((point, index) => {
    const x = scaleLinear(Number(point.x), xMin, xMax, padding, width - padding);
    const y = scaleLinear(Number(point.y), yMin, yMax, height - padding, padding);
    return `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");
}

function svgElement(name, attributes = {}) {
  const node = document.createElementNS(SVG_NS, name);
  Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, String(value)));
  return node;
}

function prepareContainer(container, label, height) {
  container.replaceChildren();
  const svg = svgElement("svg", { viewBox: `0 0 900 ${height}`, role: "img", "aria-label": label, preserveAspectRatio: "xMidYMid meet" });
  svg.classList.add("data-chart");
  container.append(svg);
  return svg;
}

function addText(svg, text, x, y, className, anchor = "start") {
  const node = svgElement("text", { x, y, class: className, "text-anchor": anchor });
  node.textContent = text;
  svg.append(node);
  return node;
}

export function renderBarChart(container, rows, { label, getLabel, getValue, language = "en", color = "#1f8a5b" } = {}) {
  const height = Math.max(320, rows.length * 42 + 70);
  const svg = prepareContainer(container, label, height);
  const margin = { top: 24, right: 85, bottom: 30, left: 205 };
  const innerWidth = 900 - margin.left - margin.right;
  const max = Math.max(...rows.map(getValue), 1);
  rows.forEach((row, index) => {
    const y = margin.top + index * 42;
    const width = (getValue(row) / max) * innerWidth;
    const bar = svgElement("rect", { x: margin.left, y, width: Math.max(width, 1), height: 25, rx: 6, fill: color, tabindex: 0 });
    const title = svgElement("title");
    title.textContent = `${getLabel(row)}: ${formatCompact(getValue(row), language)}`;
    bar.append(title);
    svg.append(bar);
    addText(svg, getLabel(row), margin.left - 12, y + 18, "axis-label", "end");
    addText(svg, formatCompact(getValue(row), language), margin.left + width + 9, y + 18, "value-label");
  });
  return svg;
}

export function renderLineChart(container, series, { label, language = "en", xLabel = (point) => point.x, yLabel = (value) => formatCompact(value, language), evidence = "observed" } = {}) {
  const width = 900;
  const height = 410;
  const margin = { top: 28, right: 28, bottom: 60, left: 76 };
  const svg = prepareContainer(container, label, height);
  const allPoints = series.flatMap((item) => item.points);
  if (!allPoints.length) return svg;
  const xValues = allPoints.map((point) => Number(point.x));
  const yValues = allPoints.map((point) => Number(point.y));
  const xMin = Math.min(...xValues);
  const xMax = Math.max(...xValues);
  const yMin = 0;
  const yMax = Math.max(...yValues, 1);
  const x = (value) => scaleLinear(Number(value), xMin, xMax, margin.left, width - margin.right);
  const y = (value) => scaleLinear(Number(value), yMin, yMax, height - margin.bottom, margin.top);
  for (let tick = 0; tick <= 4; tick += 1) {
    const value = yMax * tick / 4;
    const py = y(value);
    svg.append(svgElement("line", { x1: margin.left, x2: width - margin.right, y1: py, y2: py, class: "grid-line" }));
    addText(svg, yLabel(value), margin.left - 12, py + 4, "axis-label", "end");
  }
  const xTicks = [...new Set(allPoints.map((point) => point.x))];
  const stride = Math.max(1, Math.ceil(xTicks.length / 8));
  xTicks.filter((_, index) => index % stride === 0 || index === xTicks.length - 1).forEach((value) => {
    addText(svg, xLabel({ x: value }), x(Number(value)), height - 28, "axis-label", "middle");
  });
  series.forEach((item, seriesIndex) => {
    const style = item.style ?? evidenceStyle(item.evidence ?? evidence);
    const path = item.points.map((point, index) => `${index ? "L" : "M"}${x(point.x).toFixed(2)},${y(point.y).toFixed(2)}`).join(" ");
    svg.append(svgElement("path", { d: path, fill: "none", stroke: item.color ?? style.color, "stroke-width": 3, "stroke-dasharray": item.dash ?? style.dash, class: "series-line" }));
    item.points.forEach((point) => {
      const circle = svgElement("circle", { cx: x(point.x), cy: y(point.y), r: seriesIndex ? 3.5 : 4, fill: item.color ?? style.color, tabindex: 0 });
      const title = svgElement("title");
      title.textContent = `${item.name}: ${xLabel(point)} · ${yLabel(point.y)}`;
      circle.append(title);
      svg.append(circle);
    });
  });
  return svg;
}

export function renderGroupedBars(container, groups, { label, language = "en" } = {}) {
  const height = Math.max(320, groups.length * 60 + 75);
  const svg = prepareContainer(container, label, height);
  const margin = { top: 30, right: 100, bottom: 35, left: 190 };
  const max = Math.max(...groups.flatMap((group) => group.values.map((entry) => entry.value)), 1);
  const innerWidth = 900 - margin.left - margin.right;
  groups.forEach((group, groupIndex) => {
    const baseY = margin.top + groupIndex * 60;
    addText(svg, group.label, margin.left - 12, baseY + 24, "axis-label", "end");
    group.values.forEach((entry, valueIndex) => {
      const y = baseY + valueIndex * 22;
      const width = entry.value / max * innerWidth;
      const color = entry.color ?? (valueIndex ? "#3b4ea0" : "#1f8a5b");
      svg.append(svgElement("rect", { x: margin.left, y, width: Math.max(1, width), height: 16, rx: 4, fill: color }));
      addText(svg, formatCompact(entry.value, language), margin.left + width + 8, y + 13, "value-label");
    });
  });
  return svg;
}
