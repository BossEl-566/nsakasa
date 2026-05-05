import { Sign } from "./sign";

export type TranslationResponse = {
  input: string;
  normalizedText: string;
  matchedCount: number;
  missingWords: string[];
  signs: Sign[];
};