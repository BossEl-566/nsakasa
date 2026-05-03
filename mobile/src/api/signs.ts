import { API_BASE_URL } from "./config";
import { Sign, SignsResponse } from "../types/sign";

type FetchSignsParams = {
  search?: string;
  page?: number;
  limit?: number;
};

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

  const response = await fetch(`${API_BASE_URL}/api/signs?${params}`);

  if (!response.ok) {
    throw new Error("Failed to fetch signs");
  }

  return response.json();
}

export async function fetchSignByGloss(gloss: string): Promise<Sign> {
  const response = await fetch(
    `${API_BASE_URL}/api/signs/${encodeURIComponent(gloss)}`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch sign");
  }

  return response.json();
}