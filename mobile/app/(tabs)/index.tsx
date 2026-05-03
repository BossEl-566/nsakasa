import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { fetchSigns } from "../../src/api/signs";
import { Sign } from "../../src/types/sign";
import { router } from "expo-router";

export default function HomeScreen() {
  const [signs, setSigns] = useState<Sign[]>([]);
  const [search, setSearch] = useState("");
  const [totalSigns, setTotalSigns] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function loadSigns(searchText = search) {
    try {
      setErrorMessage("");

      const data = await fetchSigns({
        search: searchText,
        page: 1,
        limit: 20,
      });

      setSigns(data.signs);
      setTotalSigns(data.total);
    } catch (error) {
      setErrorMessage("Unable to load signs. Check if backend is running.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }

  useEffect(() => {
    loadSigns("");
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => {
      loadSigns(search);
    }, 400);

    return () => clearTimeout(timeout);
  }, [search]);

  async function handleRefresh() {
    setIsRefreshing(true);
    await loadSigns(search);
  }

  function renderSignItem({ item }: { item: Sign }) {
    return (
      <Pressable
  style={styles.card}
  onPress={() => router.push({ pathname: "/sign/[gloss]", params: { gloss: item.gloss } })}
>
        <View style={styles.cardHeader}>
          <Text style={styles.signName}>{item.displayName}</Text>
          <Text style={styles.frameText}>{item.totalFrames} frames</Text>
        </View>

        <Text style={styles.gloss}>{item.gloss}</Text>

        {item.aliases.length > 0 && (
          <Text style={styles.aliases}>
            Also searchable as: {item.aliases.join(", ")}
          </Text>
        )}
      </Pressable>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.appName}>NsaKasa</Text>
        <Text style={styles.subtitle}>Ghanaian Sign Language Dictionary</Text>
      </View>

      <View style={styles.searchBox}>
        <TextInput
          value={search}
          onChangeText={setSearch}
          placeholder="Search signs, e.g. about, quit, school"
          placeholderTextColor="#8a94a6"
          style={styles.searchInput}
        />
      </View>

      <View style={styles.summaryRow}>
        <Text style={styles.summaryText}>
          {search ? `Results for "${search}"` : "All signs"}
        </Text>
        <Text style={styles.summaryCount}>{totalSigns} total</Text>
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" />
          <Text style={styles.loadingText}>Loading signs...</Text>
        </View>
      ) : errorMessage ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>{errorMessage}</Text>
        </View>
      ) : (
        <FlatList
          data={signs}
          keyExtractor={(item) => item.id}
          renderItem={renderSignItem}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} />
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyText}>No signs found.</Text>
            </View>
          }
        />
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
    paddingBottom: 18,
  },
  appName: {
    color: "#ffffff",
    fontSize: 34,
    fontWeight: "800",
  },
  subtitle: {
    color: "#9fb0c7",
    fontSize: 15,
    marginTop: 4,
  },
  searchBox: {
    marginHorizontal: 20,
    marginBottom: 16,
    backgroundColor: "#111c2e",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#22324a",
  },
  searchInput: {
    color: "#ffffff",
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    outlineStyle: "none" as never,
  },
  summaryRow: {
    paddingHorizontal: 20,
    marginBottom: 10,
    flexDirection: "row",
    justifyContent: "space-between",
  },
  summaryText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700",
  },
  summaryCount: {
    color: "#7dd3fc",
    fontSize: 14,
    fontWeight: "700",
  },
  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
    gap: 12,
  },
  card: {
    backgroundColor: "#101b2d",
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: "#22324a",
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
  },
  signName: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "800",
    flex: 1,
  },
  frameText: {
    color: "#7dd3fc",
    fontSize: 12,
    fontWeight: "700",
  },
  gloss: {
    color: "#aab7cc",
    marginTop: 6,
    fontSize: 13,
    letterSpacing: 0.6,
  },
  aliases: {
    color: "#8190a7",
    marginTop: 8,
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
  },
  emptyText: {
    color: "#9fb0c7",
    fontSize: 15,
  },
});