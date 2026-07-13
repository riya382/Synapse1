


import { createClient } from "@supabase/supabase-js";

const supabaseUrl = "https://urqvtdzjmrhbfdidibxf.supabase.co";
const supabaseAnonKey = "sb_publishable_Wm9cZXpBXwBJ3D2aioPVSA_Ky81a2qD";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export const BUCKET_NAME = "meetings";