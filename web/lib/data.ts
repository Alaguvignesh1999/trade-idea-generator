import { readFile } from "node:fs/promises";
import path from "node:path";

import type { BacktestResult, Manifest, Snapshot } from "./types";

const baseUrl = process.env.NEXT_PUBLIC_DATA_BASE_URL;
const localRoot = path.join(process.cwd(), "public", "data");

async function loadJson<T>(relativePath: string): Promise<T> {
  if (baseUrl) {
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/${relativePath}`, {
      next: { revalidate: 300 },
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch ${relativePath}`);
    }
    return (await response.json()) as T;
  }
  const filePath = path.join(localRoot, relativePath);
  const payload = await readFile(filePath, "utf-8");
  return JSON.parse(payload) as T;
}

export async function loadManifest(): Promise<Manifest> {
  return loadJson<Manifest>("latest.json");
}

export async function loadSnapshot(snapshotPath: string): Promise<Snapshot> {
  return loadJson<Snapshot>(snapshotPath);
}

export async function loadBacktest(backtestPath: string): Promise<BacktestResult> {
  return loadJson<BacktestResult>(backtestPath);
}
