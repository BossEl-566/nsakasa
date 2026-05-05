import { router } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { translateTextToSigns } from "../../src/api/translation";
import { Sign } from "../../src/types/sign";

export default function TranslateScreen() {
  const [text, setText] = useState("");
  const [signs, setSigns] = useState<Sign[]>([]);
  const [missingWords, setMissingWords] = useState<string[]>([]);
  const [normalizedText, setNormalizedText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [hasTranslated, setHasTranslated] = useState(false);

  async function handleTranslate() {
    if (!text.trim()) {
      setErrorMessage("Type something first.");
      return;
    }

    try {
      setIsLoading(true);
      setErrorMessage("");
      setHasTranslated(true);

      const data = await translateTextToSigns(text);

      setSigns(data.signs);
      setMissingWords(data.missingWords);
      setNormalizedText(data.normalizedText);
    } catch (error) {
      setErrorMessage("Unable to translate. Check if backend is running.");
    } finally {
      setIsLoading(false);
    }
  }

  function renderSignItem({ item, index }: { item: Sign; index: number }) {
    return (
      <Pressable
        style={styles.resultCard}
        onPress={() => router.push(`/sign/${item.gloss}`)}
      >
        <View style={styles.numberBadge}>
          <Text style={styles.numberText}>{index + 1}</Text>
        </View>

        <View style={styles.resultContent}>
          <Text style={styles.signName}>{item.displayName}</Text>
          <Text style={styles.gloss}>{item.gloss}</Text>
          <Text style={styles.helperText}>Tap to watch this sign.</Text>
        </View>
      </Pressable>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Pressable style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Back</Text>
        </Pressable>

        <Text style={styles.title}>Text-to-Sign</Text>
        <Text style={styles.subtitle}>
          Type a simple English phrase and NsaKasa will match it to available
          Ghanaian Sign Language signs.
        </Text>
      </View>

      <View style={styles.inputCard}>
        <Text style={styles.inputLabel}>Enter phrase</Text>

        <TextInput
          value={text}
          onChangeText={setText}
          placeholder="Example: i am hungry"
          placeholderTextColor="#8a94a6"
          style={styles.input}
          multiline
        />

        <Pressable style={styles.translateButton} onPress={handleTranslate}>
          <Text style={styles.translateButtonText}>
            {isLoading ? "Translating..." : "Translate to Signs"}
          </Text>
        </Pressable>
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" />
          <Text style={styles.loadingText}>Finding matching signs...</Text>
        </View>
      ) : errorMessage ? (
        <View style={styles.messageCard}>
          <Text style={styles.errorText}>{errorMessage}</Text>
        </View>
      ) : hasTranslated ? (
        <View style={styles.resultsSection}>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Translation Result</Text>

            <Text style={styles.summaryText}>
              Normalized: {normalizedText || "—"}
            </Text>

            <Text style={styles.summaryText}>
              Matched signs: {signs.length}
            </Text>

            {missingWords.length > 0 && (
              <Text style={styles.missingText}>
                Missing words: {missingWords.join(", ")}
              </Text>
            )}
          </View>

          <FlatList
            data={signs}
            keyExtractor={(item) => item.id}
            renderItem={renderSignItem}
            contentContainerStyle={styles.listContent}
            ListEmptyComponent={
              <View style={styles.messageCard}>
                <Text style={styles.emptyText}>
                  No matching signs found for this phrase yet.
                </Text>
              </View>
            }
          />
        </View>
      ) : (
        <View style={styles.messageCard}>
          <Text style={styles.emptyText}>
            Try phrases like “thank you”, “i am hungry”, “where school”, or
            “mother water”.
          </Text>
        </View>
      )}
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
    paddingBottom: 16,
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
    fontSize: 34,
    fontWeight: "900",
  },
  subtitle: {
    color: "#9fb0c7",
    fontSize: 15,
    lineHeight: 22,
    marginTop: 8,
  },
  inputCard: {
    marginHorizontal: 20,
    backgroundColor: "#101b2d",
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: "#22324a",
    marginBottom: 16,
  },
  inputLabel: {
    color: "#7dd3fc",
    fontSize: 13,
    fontWeight: "900",
    textTransform: "uppercase",
    letterSpacing: 1,
    marginBottom: 10,
  },
  input: {
    minHeight: 90,
    color: "#ffffff",
    backgroundColor: "#07111f",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#22324a",
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    textAlignVertical: "top",
    outlineStyle: "none" as never,
  },
  translateButton: {
    backgroundColor: "#7dd3fc",
    borderRadius: 16,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 14,
  },
  translateButtonText: {
    color: "#07111f",
    fontSize: 15,
    fontWeight: "900",
  },
  resultsSection: {
    flex: 1,
  },
  summaryCard: {
    marginHorizontal: 20,
    backgroundColor: "#132238",
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: "#263956",
    marginBottom: 12,
  },
  summaryTitle: {
    color: "#ffffff",
    fontSize: 17,
    fontWeight: "900",
    marginBottom: 8,
  },
  summaryText: {
    color: "#aab7cc",
    fontSize: 14,
    marginTop: 4,
  },
  missingText: {
    color: "#fbbf24",
    fontSize: 14,
    marginTop: 8,
    fontWeight: "700",
  },
  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
    gap: 12,
  },
  resultCard: {
    flexDirection: "row",
    backgroundColor: "#101b2d",
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: "#22324a",
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
  numberText: {
    color: "#07111f",
    fontSize: 16,
    fontWeight: "900",
  },
  resultContent: {
    flex: 1,
  },
  signName: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "900",
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
  messageCard: {
    marginHorizontal: 20,
    backgroundColor: "#101b2d",
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: "#22324a",
  },
  emptyText: {
    color: "#9fb0c7",
    fontSize: 14,
    lineHeight: 21,
  },
  errorText: {
    color: "#fca5a5",
    fontSize: 14,
    lineHeight: 21,
  },
  center: {
    paddingVertical: 40,
    alignItems: "center",
  },
  loadingText: {
    color: "#9fb0c7",
    marginTop: 10,
  },
});