import { router } from "expo-router";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useRef } from "react";
import {
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import * as THREE from "three";

function RotatingCube() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (!meshRef.current) return;

    meshRef.current.rotation.x += 0.01;
    meshRef.current.rotation.y += 0.015;
  });

  return (
    <mesh ref={meshRef}>
      <boxGeometry args={[2, 2, 2]} />
      <meshStandardMaterial color="#7dd3fc" />
    </mesh>
  );
}

export default function AvatarTestScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Pressable style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Back</Text>
        </Pressable>

        <Text style={styles.title}>3D Avatar Test</Text>
        <Text style={styles.subtitle}>
          This confirms that the app can render 3D objects before we load the
          real signing avatar.
        </Text>
      </View>

      <View style={styles.canvasCard}>
        <Canvas camera={{ position: [0, 0, 6], fov: 50 }}>
          <ambientLight intensity={0.6} />
          <directionalLight position={[4, 4, 4]} intensity={1.2} />

          <RotatingCube />

          <OrbitControls enableZoom enablePan enableRotate />
        </Canvas>
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>What this means</Text>
        <Text style={styles.infoText}>
          If you can see a rotating cube, our 3D foundation is working. Next,
          we will replace this cube with a GLB avatar model.
        </Text>
      </View>
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
  canvasCard: {
    height: 420,
    marginHorizontal: 20,
    borderRadius: 24,
    overflow: "hidden",
    backgroundColor: "#101b2d",
    borderWidth: 1,
    borderColor: "#22324a",
  },
  infoCard: {
    margin: 20,
    backgroundColor: "#101b2d",
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: "#22324a",
  },
  infoTitle: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "900",
  },
  infoText: {
    color: "#aab7cc",
    fontSize: 14,
    lineHeight: 21,
    marginTop: 8,
  },
});