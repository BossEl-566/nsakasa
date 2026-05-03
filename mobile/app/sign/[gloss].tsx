import { useLocalSearchParams, router } from "expo-router";
import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { VideoView, useVideoPlayer } from "expo-video";

import { fetchSignByGloss } from "../../src/api/signs";
import { Sign } from "../../src/types/sign";

export default function SignDetailsScreen() {
  const { gloss } = useLocalSearchParams<{ gloss: string }>();

  const [sign, setSign] = useState<Sign | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const player = useVideoPlayer(sign?.videoUrl ?? "", (playerInstance) => {
    playerInstance.loop = true;
  });

  async function loadSign() {
    if (!gloss) {
      setErrorMessage("No sign selected.");
      setIsLoading(false);
      return;
    }

    try {
      setErrorMessage("");

      const data = await fetchSignByGloss(gloss);
      setSign(data);
    } catch (error) {
      setErrorMessage("Unable to load this sign.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadSign();
  }, [gloss]);

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <ActivityIndicator size="large" />
          <Text style={styles.loadingText}>Loading sign...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (errorMessage || !sign) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <Text style={styles.errorText}>{errorMessage || "Sign not found."}</Text>

          <Pressable style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>Go back</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Pressable style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Back</Text>
        </Pressable>

        <View style={styles.videoCard}>
          {sign.videoUrl ? (
            <VideoView
              style={styles.video}
              player={player}
              allowsFullscreen
              allowsPictureInPicture
            />
          ) : (
            <View style={styles.videoFallback}>
              <Text style={styles.videoFallbackText}>No video available</Text>
            </View>
          )}
        </View>

        <View style={styles.infoCard}>
          <Text style={styles.title}>{sign.displayName}</Text>
          <Text style={styles.gloss}>{sign.gloss}</Text>

          <View style={styles.divider} />

          <Text style={styles.label}>English</Text>
          <Text style={styles.value}>{sign.english}</Text>

          <Text style={styles.label}>Aliases</Text>
          <Text style={styles.value}>
            {sign.aliases.length ? sign.aliases.join(", ") : "None"}
          </Text>

          <Text style={styles.label}>Frames</Text>
          <Text style={styles.value}>
            {sign.totalFrames} total frames · {sign.detectedFrames} detected
          </Text>

          <Text style={styles.label}>Pose Data</Text>
          <Text style={styles.valueSmall}>
            {sign.poseDataUrl ? "Available" : "Not available"}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#07111f",
  },
  content: {
    padding: 20,
    paddingBottom: 48,
  },
  backButton: {
    alignSelf: "flex-start",
    backgroundColor: "#132238",
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#22324a",
  },
  backButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "700",
  },
  videoCard: {
    backgroundColor: "#101b2d",
    borderRadius: 24,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#22324a",
    marginBottom: 18,
  },
  video: {
    width: "100%",
    height: 360,
    backgroundColor: "#000000",
  },
  videoFallback: {
    height: 360,
    justifyContent: "center",
    alignItems: "center",
  },
  videoFallbackText: {
    color: "#9fb0c7",
  },
  infoCard: {
    backgroundColor: "#101b2d",
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: "#22324a",
  },
  title: {
    color: "#ffffff",
    fontSize: 30,
    fontWeight: "900",
  },
  gloss: {
    color: "#7dd3fc",
    marginTop: 6,
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 1,
  },
  divider: {
    height: 1,
    backgroundColor: "#22324a",
    marginVertical: 18,
  },
  label: {
    color: "#8292aa",
    fontSize: 13,
    fontWeight: "800",
    marginTop: 14,
    textTransform: "uppercase",
    letterSpacing: 0.8,
  },
  value: {
    color: "#ffffff",
    fontSize: 17,
    marginTop: 5,
  },
  valueSmall: {
    color: "#aab7cc",
    fontSize: 14,
    marginTop: 5,
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 24,
  },
  loadingText: {
    color: "#9fb0c7",
    marginTop: 10,
  },
  errorText: {
    color: "#fca5a5",
    textAlign: "center",
    fontSize: 15,
    marginBottom: 16,
  },
});