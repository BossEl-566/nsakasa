import mongoose, { Schema, Document } from "mongoose";

export interface ISign extends Document {
  gloss: string;
  displayName: string;
  english: string;
  aliases: string[];
  baseWord: string;
  variant?: number | null;

  videoFile?: string | null;
  videoRawPath?: string | null;
  poseSequenceFile?: string | null;

  totalFrames: number;
  detectedFrames: number;
  missingDetectionFrames: number;

  bodyPointsPerFrame: number;
  handPointsPerFrame: number;
  facePointsAvailable: boolean;

  status: string;
}

const SignSchema = new Schema<ISign>(
  {
    gloss: {
      type: String,
      required: true,
      unique: true,
      uppercase: true,
      trim: true,
    },

    displayName: {
      type: String,
      required: true,
      trim: true,
    },

    english: {
      type: String,
      required: true,
      lowercase: true,
      trim: true,
    },

    aliases: {
      type: [String],
      default: [],
      index: true,
    },

    baseWord: {
      type: String,
      required: true,
      lowercase: true,
      trim: true,
      index: true,
    },

    variant: {
      type: Number,
      default: null,
    },

    videoFile: {
      type: String,
      default: null,
    },

    videoRawPath: {
      type: String,
      default: null,
    },

    poseSequenceFile: {
      type: String,
      default: null,
    },

    totalFrames: {
      type: Number,
      default: 0,
    },

    detectedFrames: {
      type: Number,
      default: 0,
    },

    missingDetectionFrames: {
      type: Number,
      default: 0,
    },

    bodyPointsPerFrame: {
      type: Number,
      default: 25,
    },

    handPointsPerFrame: {
      type: Number,
      default: 21,
    },

    facePointsAvailable: {
      type: Boolean,
      default: false,
    },

    status: {
      type: String,
      default: "processed",
    },
  },
  {
    timestamps: true,
  }
);

export const Sign = mongoose.model<ISign>("Sign", SignSchema);