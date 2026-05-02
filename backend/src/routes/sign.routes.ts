import express from "express";
import { Sign } from "../models/sign.model.js";

const router = express.Router();

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

router.get("/", async (req, res) => {
  try {
    const search = String(req.query.search ?? "").trim();
    const normalizedSearch = search.toLowerCase();

    let filter = {};

    if (search) {
      const escapedSearch = escapeRegex(normalizedSearch);

      // Matches normal words safely.
      // Example: "quit" matches "quit", "withdrawal or quit"
      // But it will not match "mosquito".
      const wordBoundaryRegex = new RegExp(`(^|\\s|/|-)${escapedSearch}(\\s|/|-|$)`, "i");

      // Matches dataset gloss style.
      // Example: quit matches QUIT and WITHDRAWAL_OR_QUIT
      const glossBoundaryRegex = new RegExp(`(^|_)${escapeRegex(search.toUpperCase())}(_|$)`, "i");

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

    const signs = await Sign.find(filter).sort({ displayName: 1 }).limit(50);

    res.json({
      count: signs.length,
      search,
      signs,
    });
  } catch (error) {
    res.status(500).json({
      message: "Failed to fetch signs",
      error,
    });
  }
});

export default router;