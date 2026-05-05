import { API_BASE_URL } from "./config";
import { TranslationResponse } from "../types/translation";

export async function translateTextToSigns(
  text: string
): Promise<TranslationResponse> {
  const params = new URLSearchParams({
    text,
  });

  const response = await fetch(`${API_BASE_URL}/api/translate?${params}`);

  if (!response.ok) {
    throw new Error("Failed to translate text");
  }

  return response.json();
}