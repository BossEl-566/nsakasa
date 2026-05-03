export type Sign = {
  id: string;
  gloss: string;
  displayName: string;
  english: string;
  aliases: string[];
  baseWord: string;
  variant: number | null;

  videoUrl: string | null;
  poseDataUrl: string | null;

  videoFile: string | null;
  poseSequenceFile: string | null;

  totalFrames: number;
  detectedFrames: number;
  missingDetectionFrames: number;

  bodyPointsPerFrame: number;
  handPointsPerFrame: number;
  facePointsAvailable: boolean;

  status: string;
};

export type SignsResponse = {
  count: number;
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  search: string;
  signs: Sign[];
};