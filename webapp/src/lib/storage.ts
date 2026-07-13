import { supabase, BUCKET_NAME } from "./supabase";

export async function uploadFileToFirebase(
  file: File,
  name: string,
  setProgress?: (progress: number) => void,
): Promise<string> {
  try {
    if (setProgress) {
      setProgress(10);
    }

    const { data, error } = await supabase.storage
      .from(BUCKET_NAME)
      .upload(name, file, {
        cacheControl: "3600",
        upsert: true,
      });

    if (error) {
      throw error;
    }

    if (setProgress) {
      setProgress(90);
    }

    const { data: urlData } = supabase.storage
      .from(BUCKET_NAME)
      .getPublicUrl(data.path);

    if (setProgress) {
      setProgress(100);
    }

    console.log("File available at", urlData.publicUrl);
    return urlData.publicUrl;
  } catch (error) {
    console.error(error);
    throw error;
  }
}