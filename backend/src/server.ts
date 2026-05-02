import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import path from "path";
import { connectDB } from "./config/db.js";
import signRoutes from "./routes/sign.routes.js";

dotenv.config();

const app = express();

const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

const rawSignsPath = path.join(
  process.cwd(),
  "..",
  "data",
  "raw",
  "GSL_openpose_data"
);

app.use("/media/signs", express.static(rawSignsPath));

app.use("/api/signs", signRoutes);

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