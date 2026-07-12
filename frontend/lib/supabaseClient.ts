import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

let cachedClient: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient | null {
	if (cachedClient) {
		return cachedClient;
	}

	if (!supabaseUrl || !supabaseAnonKey) {
		return null;
	}

	cachedClient = createClient(supabaseUrl, supabaseAnonKey, {
		realtime: {
			params: {
				eventsPerSecond: 10,
			},
		},
	});

	return cachedClient;
}

export const supabaseClient = getSupabaseClient();
