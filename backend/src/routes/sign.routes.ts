import express from "express";
import { Sign } from "../models/sign.model.js";

const router = express.Router();

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function buildSignResponse(req: express.Request, sign: any) {
  const baseUrl = `${req.protocol}://${req.get("host")}`;

  const videoUrl = sign.videoFile
    ? `${baseUrl}/media/signs/${encodeURIComponent(sign.gloss)}/${encodeURIComponent(sign.videoFile)}`
    : null;

  const poseDataUrl = sign.poseSequenceFile
    ? `${baseUrl}/media/poses/${encodeURIComponent(sign.gloss)}/${encodeURIComponent(sign.poseSequenceFile)}`
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

    videoFile: sign.videoFile,
    poseSequenceFile: sign.poseSequenceFile,

    totalFrames: sign.totalFrames,
    detectedFrames: sign.detectedFrames,
    missingDetectionFrames: sign.missingDetectionFrames,

    bodyPointsPerFrame: sign.bodyPointsPerFrame,
    handPointsPerFrame: sign.handPointsPerFrame,
    facePointsAvailable: sign.facePointsAvailable,

    status: sign.status,
  };
}

router.get("/", async (req, res) => {
  try {
    const search = String(req.query.search ?? "").trim();
    const normalizedSearch = search.toLowerCase();

    const page = Math.max(Number(req.query.page) || 1, 1);
    const limit = Math.min(Math.max(Number(req.query.limit) || 20, 1), 100);
    const skip = (page - 1) * limit;

    let filter = {};

    if (search) {
      const escapedSearch = escapeRegex(normalizedSearch);

      const wordBoundaryRegex = new RegExp(
        `(^|\\s|/|-)${escapedSearch}(\\s|/|-|$)`,
        "i"
      );

      const glossBoundaryRegex = new RegExp(
        `(^|_)${escapeRegex(search.toUpperCase())}(_|$)`,
        "i"
      );

      filter = {
        $or: [
          { aliases: normalizedSearch },
          { baseWord: normalizedSearch },
          { english: normalizedSearch },
          { gloss: glossBoundaryRegex },
          { displayName: wordBoundaryRegex },
          { english: wordBoundaryRegex },
          { baseWord: wordBoundaryRegex },
          { aliases: wordBoundaryRegex },
        ],
      };
    }

    const total = await Sign.countDocuments(filter);

    const signs = await Sign.find(filter)
      .sort({ displayName: 1 })
      .skip(skip)
      .limit(limit)
      .lean();

    res.json({
      count: signs.length,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
      hasNextPage: page * limit < total,
      hasPreviousPage: page > 1,
      search,
      signs: signs.map((sign) => buildSignResponse(req, sign)),
    });
  } catch (error) {
    res.status(500).json({
      message: "Failed to fetch signs",
      error,
    });
  }
});

router.get("/:gloss", async (req, res) => {
  try {
    const gloss = req.params.gloss.toUpperCase();

    const sign = await Sign.findOne({ gloss }).lean();

    if (!sign) {
      return res.status(404).json({
        message: "Sign not found",
      });
    }

    res.json(buildSignResponse(req, sign));
  } catch (error) {
    res.status(500).json({
      message: "Failed to fetch sign",
      error,
    });
  }
});

export default router;