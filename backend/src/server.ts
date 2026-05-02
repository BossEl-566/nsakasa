import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { connectDB } from "./config/db.js";

dotenv.config();

const app = express();

const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.json({
    message: "NsaKasa backend is running",
    database: "connected",
    status: "ok",
  });
});

async function startServer() {
  await connectDB();

  app.listen(PORT, () => {
    console.log(`NsaKasa backend running on port ${PORT}`);
  });
}

startServer();