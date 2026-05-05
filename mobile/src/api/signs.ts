import { API_BASE_URL } from "./config";
import { Sign, SignsResponse } from "../types/sign";

type FetchSignsParams = {
  search?: string;
  page?: number;
  limit?: number;
};

async function fetchWithTimeout(url: string, timeoutMs = 10000) {
  const controller = new AbortController();

  const timeout = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
    });

    return response;
  } finally {
    clearTimeout(timeout);
  }
}

export async function fetchSigns({
  search = "",
  page = 1,
  limit = 20,
}: FetchSignsParams = {}): Promise<SignsResponse> {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
  });

  if (search.trim()) {
    params.set("search", search.trim());
  }

  const url = `${API_BASE_URL}/api/signs?${params.toString()}`;

  console.log("Fetching signs from:", url);

  const response = await fetchWithTimeout(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch signs. Status: ${response.status}`);
  }

  const data = await response.json();

  console.log("Fetched signs:", data);

  return data;
}

export async function fetchSignByGloss(gloss: string): Promise<Sign> {
  const url = `${API_BASE_URL}/api/signs/${encodeURIComponent(gloss)}`;

  console.log("Fetching sign by gloss from:", url);

  const response = await fetchWithTimeout(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch sign. Status: ${response.status}`);
  }

  const data = await response.json();

  console.log("Fetched sign:", data);

  return data;
}