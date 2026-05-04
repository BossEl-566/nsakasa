import { router, useFocusEffect } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { fetchSignByGloss } from "../../src/api/signs";
import { Sign } from "../../src/types/sign";
import { getPracticedSigns } from "../../src/utils/progress";

const BEGINNER_LESSON_SIGNS = [
  "THANK_YOU",
  "PLEASE",
  "SORRY",
  "YES",
  "NO",
  "HELP",
  "WATER",
  "HUNGRY",
  "SCHOOL",
  "MOTHER",
];

export default function LearnScreen() {
  const [signs, setSigns] = useState<Sign[]>([]);
  const [practicedSigns, setPracticedSigns] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  async function loadPracticedSigns() {
    const savedPracticedSigns = await getPracticedSigns();
    setPracticedSigns(savedPracticedSigns);
  }

  async function loadLessonSigns() {
    try {
      setErrorMessage("");

      const results = await Promise.allSettled(
        BEGINNER_LESSON_SIGNS.map((gloss) => fetchSignByGloss(gloss))
      );

      const successfulSigns: Sign[] = [];
      const failedSigns: string[] = [];

      results.forEach((result, index) => {
        const gloss = BEGINNER_LESSON_SIGNS[index];

        if (result.status === "fulfilled") {
          successfulSigns.push(result.value);
        } else {
          failedSigns.push(gloss);
        }
      });

      console.log("Failed beginner signs:", failedSigns);

      if (successfulSigns.length === 0) {
        setErrorMessage("No beginner lesson signs could be loaded.");
        return;
      }

      setSigns(successfulSigns);
      await loadPracticedSigns();
    } catch (error) {
      setErrorMessage("Unable to load beginner lesson signs.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadLessonSigns();
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadPracticedSigns();
    }, [])
  );

  const practicedCount = signs.filter((sign) =>
    practicedSigns.includes(sign.gloss)
  ).length;

  function renderSignItem({ item, index }: { item: Sign; index: number }) {
    const isPracticed = practicedSigns.includes(item.gloss);

    return (
      <Pressable
        style={isPracticed ? styles.cardPracticed : styles.card}
        onPress={() => router.push(`/sign/${item.gloss}`)}
      >
        <View style={isPracticed ? styles.numberBadgeDone : styles.numberBadge}>
          <Text style={isPracticed ? styles.numberTextDone : styles.numberText}>
            {isPracticed ? "✓" : index + 1}
          </Text>
        </View>

        <View style={styles.cardContent}>
          <View style={styles.cardTitleRow}>
            <Text style={styles.signName}>{item.displayName}</Text>

            {isPracticed && (
              <Text style={styles.doneText}>Practiced</Text>
            )}
          </View>

          <Text style={styles.gloss}>{item.gloss}</Text>

          <Text style={styles.helperText}>
            {isPracticed
              ? "Good work. Tap to review this sign again."
              : "Tap to watch, replay, and practice slowly."}
          </Text>
        </View>
      </Pressable>
    );
  }

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <ActivityIndicator size="large" />
          <Text style={styles.loadingText}>Loading beginner lesson...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (errorMessage) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <Text style={styles.errorText}>{errorMessage}</Text>

          <Pressable style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>Go back</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Pressable style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Back</Text>
        </Pressable>

        <Text style={styles.title}>Beginner Learning Mode</Text>
        <Text style={styles.subtitle}>
          Start with common signs parents, children, and beginners can use every
          day.
        </Text>

        <View style={styles.lessonInfoCard}>
          <View style={styles.lessonTopRow}>
            <View>
              <Text style={styles.lessonLabel}>Lesson 1</Text>
              <Text style={styles.lessonTitle}>Basic Communication</Text>
            </View>

            <View style={styles.progressBadge}>
              <Text style={styles.progressText}>
                {practicedCount}/{signs.length}
              </Text>
            </View>
          </View>

          <Text style={styles.lessonDescription}>
            Learn simple signs for greeting, asking, responding, and expressing
            basic needs.
          </Text>

          <View style={styles.progressBarBackground}>
            <View
              style={[
                styles.progressBarFill,
                {
                  width:
                    signs.length > 0
                      ? `${(practicedCount / signs.length) * 100}%`
                      : "0%",
                },
              ]}
            />
          </View>

          <Text style={styles.progressLabel}>
            {practicedCount === signs.length
              ? "Lesson completed. Great job."
              : `${signs.length - practicedCount} signs left to practice.`}
          </Text>
        </View>
      </View>

      <FlatList
        data={signs}
        keyExtractor={(item) => item.id}
        renderItem={renderSignItem}
        contentContainerStyle={styles.listContent}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#07111f",
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 12,
  },
  backButton: {
    alignSelf: "flex-start",
    backgroundColor: "#132238",
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginBottom: 18,
    borderWidth: 1,
    borderColor: "#22324a",
  },
  backButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "700",
  },
  title: {
    color: "#ffffff",
    fontSize: 32,
    fontWeight: "900",
  },
  subtitle: {
    color: "#9fb0c7",
    fontSize: 15,
    lineHeight: 22,
    marginTop: 8,
  },
  lessonInfoCard: {
    backgroundColor: "#101b2d",
    borderRadius: 22,
    padding: 18,
    marginTop: 20,
    borderWidth: 1,
    borderColor: "#22324a",
  },
  lessonTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 16,
    alignItems: "flex-start",
  },
  lessonLabel: {
    color: "#7dd3fc",
    fontSize: 13,
    fontWeight: "900",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  lessonTitle: {
    color: "#ffffff",
    fontSize: 22,
    fontWeight: "900",
    marginTop: 8,
  },
  lessonDescription: {
    color: "#aab7cc",
    fontSize: 14,
    lineHeight: 21,
    marginTop: 8,
  },
  progressBadge: {
    backgroundColor: "#132238",
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: "#263956",
  },
  progressText: {
    color: "#7dd3fc",
    fontSize: 14,
    fontWeight: "900",
  },
  progressBarBackground: {
    height: 10,
    backgroundColor: "#132238",
    borderRadius: 999,
    overflow: "hidden",
    marginTop: 18,
  },
  progressBarFill: {
    height: "100%",
    backgroundColor: "#7dd3fc",
    borderRadius: 999,
  },
  progressLabel: {
    color: "#8190a7",
    fontSize: 13,
    marginTop: 10,
  },
  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
    gap: 12,
  },
  card: {
    flexDirection: "row",
    backgroundColor: "#101b2d",
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: "#22324a",
    gap: 14,
  },
  cardPracticed: {
    flexDirection: "row",
    backgroundColor: "#0f241c",
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: "#22c55e",
    gap: 14,
  },
  numberBadge: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: "#7dd3fc",
    alignItems: "center",
    justifyContent: "center",
  },
  numberBadgeDone: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: "#22c55e",
    alignItems: "center",
    justifyContent: "center",
  },
  numberText: {
    color: "#07111f",
    fontSize: 16,
    fontWeight: "900",
  },
  numberTextDone: {
    color: "#052e16",
    fontSize: 17,
    fontWeight: "900",
  },
  cardContent: {
    flex: 1,
  },
  cardTitleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 10,
    alignItems: "center",
  },
  signName: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "900",
    flex: 1,
  },
  doneText: {
    color: "#86efac",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  gloss: {
    color: "#7dd3fc",
    marginTop: 5,
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
  helperText: {
    color: "#8190a7",
    marginTop: 7,
    fontSize: 13,
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