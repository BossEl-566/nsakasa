import AsyncStorage from "@react-native-async-storage/async-storage";

const PRACTICED_SIGNS_KEY = "nsakasa_practiced_signs";

export async function getPracticedSigns(): Promise<string[]> {
  const storedValue = await AsyncStorage.getItem(PRACTICED_SIGNS_KEY);

  if (!storedValue) {
    return [];
  }

  try {
    return JSON.parse(storedValue);
  } catch {
    return [];
  }
}

export async function isSignPracticed(gloss: string): Promise<boolean> {
  const practicedSigns = await getPracticedSigns();

  return practicedSigns.includes(gloss);
}

export async function markSignAsPracticed(gloss: string): Promise<string[]> {
  const practicedSigns = await getPracticedSigns();

  if (practicedSigns.includes(gloss)) {
    return practicedSigns;
  }

  const updatedSigns = [...practicedSigns, gloss];

  await AsyncStorage.setItem(PRACTICED_SIGNS_KEY, JSON.stringify(updatedSigns));

  return updatedSigns;
}

export async function unmarkSignAsPracticed(gloss: string): Promise<string[]> {
  const practicedSigns = await getPracticedSigns();

  const updatedSigns = practicedSigns.filter((item) => item !== gloss);

  await AsyncStorage.setItem(PRACTICED_SIGNS_KEY, JSON.stringify(updatedSigns));

  return updatedSigns;
}