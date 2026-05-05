import { Href, Link } from "expo-router";
import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
  Pressable,
} from "react-native";

import { fetchSigns } from "../../src/api/signs";
import { Sign } from "../../src/types/sign";

export default function HomeScreen() {
  const [signs, setSigns] = useState<Sign[]>([]);
  const [search, setSearch] = useState("");
  const [totalSigns, setTotalSigns] = useState(0);

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [isLoading, setIsLoading] = useState(true);
  const [hasInitialLoaded, setHasInitialLoaded] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const [errorMessage, setErrorMessage] = useState("");

  console.log("HomeScreen rendered with state:")

  async function loadSigns({
    searchText = search,
    nextPage = 1,
    shouldReset = false,
  }: {
    searchText?: string;
    nextPage?: number;
    shouldReset?: boolean;
  }) {
    try {
      console.log("loadSigns started:", {
        searchText,
        nextPage,
        shouldReset,
      });

      setErrorMessage("");

      if (shouldReset) {
        setIsLoading(true);
      }

      const data = await fetchSigns({
        search: searchText,
        page: nextPage,
        limit: 20,
      });

      console.log("loadSigns received:", data);

      setSigns((currentSigns) => {
        if (shouldReset || nextPage === 1) {
          return data.signs;
        }

        return [...currentSigns, ...data.signs];
      });

      setTotalSigns(data.total);
      setPage(data.page);
      setTotalPages(data.totalPages);
    } catch (error) {
      console.log("loadSigns error:", error);
      setErrorMessage("Unable to load signs. Check if backend is running.");
    } finally {
      console.log("loadSigns finished");
      setIsLoading(false);
      setIsRefreshing(false);
      setIsLoadingMore(false);
    }
  }

  useEffect(() => {
    async function initialLoad() {
      await loadSigns({
        searchText: "",
        nextPage: 1,
        shouldReset: true,
      });

      setHasInitialLoaded(true);
    }

    initialLoad();
  }, []);

  useEffect(() => {
    if (!hasInitialLoaded) return;

    const timeout = setTimeout(() => {
      loadSigns({
        searchText: search,
        nextPage: 1,
        shouldReset: true,
      });
    }, 400);

    return () => clearTimeout(timeout);
  }, [search, hasInitialLoaded]);

  async function handleRefresh() {
    setIsRefreshing(true);

    await loadSigns({
      searchText: search,
      nextPage: 1,
      shouldReset: true,
    });
  }

  async function handleLoadMore() {
    if (isLoading || isLoadingMore || page >= totalPages) return;

    setIsLoadingMore(true);

    await loadSigns({
      searchText: search,
      nextPage: page + 1,
      shouldReset: false,
    });
  }

  function renderHeader() {
    return (
      <View>
        <View style={styles.header}>
          <Text style={styles.appName}>NsaKasa</Text>
          <Text style={styles.subtitle}>Ghanaian Sign Language Dictionary</Text>
        </View>

        <Link href={"/avatar-test" as Href} asChild>
          <Pressable style={styles.avatarCard}>
            <View style={styles.cardTextBlock}>
              <Text style={styles.avatarLabel}>3D Mode</Text>
              <Text style={styles.avatarTitle}>Test 3D Avatar</Text>
              <Text style={styles.avatarDescription}>
                Confirm 3D rendering before loading the signing character.
              </Text>
            </View>

            <Text style={styles.avatarArrow}>→</Text>
          </Pressable>
        </Link>

        <Link href={"/translate" as Href} asChild>
          <Pressable style={styles.translateCard}>
            <View style={styles.cardTextBlock}>
              <Text style={styles.translateLabel}>Translation Mode</Text>
              <Text style={styles.translateTitle}>Text to Sign</Text>
              <Text style={styles.translateDescription}>
                Type a simple phrase and match it to GSL signs.
              </Text>
            </View>

            <Text style={styles.translateArrow}>→</Text>
          </Pressable>
        </Link>

        <Link href={"/learn" as Href} asChild>
          <Pressable style={styles.learnCard}>
            <View style={styles.cardTextBlock}>
              <Text style={styles.learnLabel}>Beginner Mode</Text>
              <Text style={styles.learnTitle}>Start Learning GSL</Text>
              <Text style={styles.learnDescription}>
                Learn basic signs for everyday communication.
              </Text>
            </View>

            <Text style={styles.learnArrow}>→</Text>
          </Pressable>
        </Link>

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
          <View>
            <Text style={styles.summaryText}>
              {search ? `Results for "${search}"` : "All signs"}
            </Text>

            <Text style={styles.pageText}>
              Page {page} of {totalPages}
            </Text>
          </View>

          <Text style={styles.summaryCount}>{totalSigns} total</Text>
        </View>
      </View>
    );
  }

  function renderSignItem({ item }: { item: Sign }) {
    return (
      <Link
        href={{
          pathname: "/sign/[gloss]",
          params: { gloss: item.gloss },
        }}
        asChild
      >
        <Pressable style={styles.card}>
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
      </Link>
    );
  }

  function renderFooter() {
    if (isLoadingMore) {
      return (
        <View style={styles.footer}>
          <ActivityIndicator />
          <Text style={styles.footerText}>Loading more signs...</Text>
        </View>
      );
    }

    if (!isLoading && signs.length > 0 && page >= totalPages) {
      return (
        <View style={styles.footer}>
          <Text style={styles.footerText}>You have reached the end.</Text>
        </View>
      );
    }

    return null;
  }

  function renderEmptyState() {
    if (isLoading) {
      return (
        <View style={styles.centerInList}>
          <ActivityIndicator size="large" />
          <Text style={styles.loadingText}>Loading signs...</Text>
        </View>
      );
    }

    if (errorMessage) {
      return (
        <View style={styles.centerInList}>
          <Text style={styles.errorText}>{errorMessage}</Text>
        </View>
      );
    }

    return (
      <View style={styles.centerInList}>
        <Text style={styles.emptyText}>No signs found.</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={isLoading || errorMessage ? [] : signs}
        keyExtractor={(item) => item.id}
        renderItem={renderSignItem}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={renderEmptyState}
        ListFooterComponent={renderFooter}
        contentContainerStyle={styles.listContent}
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.4}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} />
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#07111f",
  },
  listContent: {
    paddingBottom: 40,
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
  cardTextBlock: {
    flex: 1,
  },

  avatarCard: {
    marginHorizontal: 20,
    marginBottom: 16,
    backgroundColor: "#16251b",
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: "#22c55e",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 16,
  },
  avatarLabel: {
    color: "#86efac",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  avatarTitle: {
    color: "#ffffff",
    fontSize: 21,
    fontWeight: "900",
    marginTop: 6,
  },
  avatarDescription: {
    color: "#bbf7d0",
    fontSize: 14,
    marginTop: 6,
  },
  avatarArrow: {
    color: "#86efac",
    fontSize: 28,
    fontWeight: "900",
  },

  translateCard: {
    marginHorizontal: 20,
    marginBottom: 16,
    backgroundColor: "#1f1738",
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: "#6d5dfc",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 16,
  },
  translateLabel: {
    color: "#c4b5fd",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  translateTitle: {
    color: "#ffffff",
    fontSize: 21,
    fontWeight: "900",
    marginTop: 6,
  },
  translateDescription: {
    color: "#c4b5fd",
    fontSize: 14,
    marginTop: 6,
  },
  translateArrow: {
    color: "#c4b5fd",
    fontSize: 28,
    fontWeight: "900",
  },

  learnCard: {
    marginHorizontal: 20,
    marginBottom: 16,
    backgroundColor: "#0f2a3d",
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: "#1f5f7a",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 16,
  },
  learnLabel: {
    color: "#7dd3fc",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  learnTitle: {
    color: "#ffffff",
    fontSize: 21,
    fontWeight: "900",
    marginTop: 6,
  },
  learnDescription: {
    color: "#aab7cc",
    fontSize: 14,
    marginTop: 6,
  },
  learnArrow: {
    color: "#7dd3fc",
    fontSize: 28,
    fontWeight: "900",
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
    alignItems: "flex-end",
  },
  summaryText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700",
  },
  pageText: {
    color: "#8190a7",
    fontSize: 12,
    marginTop: 4,
  },
  summaryCount: {
    color: "#7dd3fc",
    fontSize: 14,
    fontWeight: "700",
  },

  card: {
    marginHorizontal: 20,
    marginBottom: 12,
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

  footer: {
    paddingVertical: 22,
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  footerText: {
    color: "#8190a7",
    fontSize: 13,
  },
  centerInList: {
    paddingVertical: 60,
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