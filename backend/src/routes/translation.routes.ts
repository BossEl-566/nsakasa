import express from "express";
import { Sign } from "../models/sign.model.js";

const router = express.Router();

function normalizeText(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, " ")
    .replace(/-/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function buildSignResponse(req: express.Request, sign: any) {
  const baseUrl = `${req.protocol}://${req.get("host")}`;

  const videoUrl = sign.videoFile
    ? `${baseUrl}/media/signs/${encodeURIComponent(sign.gloss)}/${encodeURIComponent(
        sign.videoFile
      )}`
    : null;

  const poseDataUrl = sign.poseSequenceFile
    ? `${baseUrl}/media/poses/${encodeURIComponent(sign.gloss)}/${encodeURIComponent(
        sign.poseSequenceFile
      )}`
    : null;

  return {
    id: sign._id,
    gloss: sign.gloss,
    displayName: sign.displayName,
    english: sign.english,
    aliases: sign.aliases,
    baseWord: sign.baseWord,
    variant: sign.variant,
    videoUrl,
    poseDataUrl,
    totalFrames: sign.totalFrames,
    detectedFrames: sign.detectedFrames,
    missingDetectionFrames: sign.missingDetectionFrames,
    status: sign.status,
  };
}

function uniqueList(items: string[]) {
  return Array.from(new Set(items.filter(Boolean)));
}

const STOP_WORDS = new Set([
  "a",
  "an",
  "the",
  "is",
  "am",
  "are",
  "was",
  "were",
  "be",
  "been",
]);

router.get("/", async (req, res) => {
  try {
    const text = String(req.query.text ?? "").trim();

    if (!text) {
      return res.status(400).json({
        message: "Text is required. Example: /api/translate?text=thank you",
      });
    }

    const normalizedText = normalizeText(text);
    const tokens = normalizedText.split(" ").filter(Boolean);

    const signs = await Sign.find().sort({ displayName: 1 }).lean();

    const dictionary = signs.flatMap((sign) => {
      const possibleTexts = uniqueList([
        sign.english,
        sign.baseWord,
        sign.displayName,
        ...(sign.aliases ?? []),
      ]);

      return possibleTexts.map((item) => ({
        text: normalizeText(item),
        tokens: normalizeText(item).split(" ").filter(Boolean),
        sign,
      }));
    });

    dictionary.sort((a, b) => {
      if (b.tokens.length !== a.tokens.length) {
        return b.tokens.length - a.tokens.length;
      }

      return b.text.length - a.text.length;
    });

    const matchedSigns: any[] = [];
    const missingWords: string[] = [];

    let index = 0;

    while (index < tokens.length) {
      const currentToken = tokens[index];

      if (!currentToken || STOP_WORDS.has(currentToken)) {
        index += 1;
        continue;
      }

      const match = dictionary.find((entry) => {
        const slice = tokens.slice(index, index + entry.tokens.length);

        return entry.tokens.join(" ") === slice.join(" ");
      });

      if (match) {
        matchedSigns.push(match.sign);
        index += match.tokens.length;
      } else {
        missingWords.push(currentToken);
        index += 1;
      }
    }

    res.json({
      input: text,
      normalizedText,
      matchedCount: matchedSigns.length,
      missingWords: uniqueList(missingWords),
      signs: matchedSigns.map((sign) => buildSignResponse(req, sign)),
    });
  } catch (error) {
    res.status(500).json({
      message: "Translation failed",
      error,
    });
  }
});

export default router;