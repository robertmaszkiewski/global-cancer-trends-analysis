function normaliseBase(baseUrl) {
  return String(baseUrl).replace(/\/$/, "");
}

function routeMatches(route, query) {
  return Object.entries(query).every(([key, value]) => value == null || key === "family" && route.family === value || route[key] === value);
}

export function rowsToObjects(partition) {
  if (!partition?.schema || !partition?.rows) return [];
  return partition.rows.map((row) => Object.fromEntries(partition.schema.map((name, index) => [name, row[index]])));
}

export class DataClient {
  constructor({ baseUrl = globalThis.CANCER_DATA_BASE ?? "../data/web", fetchFn = globalThis.fetch?.bind(globalThis) } = {}) {
    if (!fetchFn) throw new Error("A fetch implementation is required");
    this.baseUrl = normaliseBase(baseUrl);
    this.fetchFn = fetchFn;
    this.cache = new Map();
    this.partitionCache = new Map();
    this.manifest = null;
    this.routes = [];
    this.starter = null;
  }

  async fetchJson(path) {
    const url = `${this.baseUrl}/${path}`;
    if (this.cache.has(url)) return this.cache.get(url);
    const promise = this.fetchFn(url).then(async (response) => {
      if (!response.ok) throw new Error(`Data request failed (${response.status}): ${url}`);
      return response.json();
    });
    this.cache.set(url, promise);
    try {
      return await promise;
    } catch (error) {
      this.cache.delete(url);
      throw error;
    }
  }

  async initialise() {
    const [manifest, routeIndex, starter] = await Promise.all([
      this.fetchJson("manifest.json"),
      this.fetchJson("routes.json"),
      this.fetchJson("starter.json"),
    ]);
    this.manifest = manifest;
    this.routes = routeIndex.routes ?? [];
    this.starter = starter;
    return this;
  }

  findRoute(query) {
    return this.routes.find((route) => routeMatches(route, query));
  }

  availableValues(key, constraints = {}) {
    return [...new Set(this.routes.filter((route) => routeMatches(route, constraints)).map((route) => route[key]).filter(Boolean))].sort();
  }

  hasRoute(query) {
    return Boolean(this.findRoute(query));
  }

  async load(query) {
    const route = this.findRoute(query);
    if (!route) return { available: false, reason: "combination_unavailable" };
    if (this.partitionCache.has(route.file)) return this.partitionCache.get(route.file);
    const partition = await this.fetchJson(route.file);
    const result = { ...partition, available: true, route, objects: rowsToObjects(partition) };
    this.partitionCache.set(route.file, result);
    return result;
  }
}
