import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import { connectDB } from "../config/db.js";
import { Sign } from "../models/sign.model.js";

dotenv.config();

async function seedSigns() {
  try {
    await connectDB();

    const catalogPath = path.join(
      process.cwd(),
      "..",
      "data",
      "processed",
      "sign_catalog.json"
    );

    if (!fs.existsSync(catalogPath)) {
      throw new Error(`sign_catalog.json not found at: ${catalogPath}`);
    }

    const rawCatalog = fs.readFileSync(catalogPath, "utf-8");
    const signs = JSON.parse(rawCatalog);

    console.log(`Found ${signs.length} signs in catalog.`);

    let createdOrUpdated = 0;

    for (const sign of signs) {
      await Sign.findOneAndUpdate(
        { gloss: sign.gloss },
        {
          gloss: sign.gloss,
          displayName: sign.displayName,
          english: sign.english,
          aliases: sign.aliases,
          baseWord: sign.baseWord,
          variant: sign.variant,

          videoFile: sign.videoFile,
          videoRawPath: sign.videoRawPath,
          poseSequenceFile: sign.poseSequenceFile,

          totalFrames: sign.totalFrames,
          detectedFrames: sign.detectedFrames,
          missingDetectionFrames: sign.missingDetectionFrames,

          bodyPointsPerFrame: sign.bodyPointsPerFrame,
          handPointsPerFrame: sign.handPointsPerFrame,
          facePointsAvailable: sign.facePointsAvailable,

          status: sign.status,
        },
        {
          upsert: true,
          new: true,
        }
      );

      createdOrUpdated += 1;
    }

    console.log(`Seed complete. Created/updated ${createdOrUpdated} signs.`);

    process.exit(0);
  } catch (error) {
    console.error("Seed failed:", error);
    process.exit(1);
  }
}

seedSigns();