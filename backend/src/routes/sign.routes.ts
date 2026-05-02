import express from "express";
import { Sign } from "../models/sign.model.js";

const router = express.Router();

router.get("/", async (req, res) => {
  try {
    const signs = await Sign.find()
      .sort({ displayName: 1 })
      .limit(50);

    res.json({
      count: signs.length,
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