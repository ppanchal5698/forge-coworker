'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { type RealtimeChannel } from '@supabase/supabase-js';

import { getSupabaseClient } from '@/lib/supabaseClient';

export interface UseSupabaseRealtimeOptions {
  schema?: string;
  table: string;
  event?: 'INSERT' | 'UPDATE' | 'DELETE' | '*';
  filter?: string;
  enabled?: boolean;
  maxItems?: number;
}

export function useSupabaseRealtime<T = Record<string, unknown>>(
  channelName: string,
  options: UseSupabaseRealtimeOptions
) {
  const {
    schema = 'public',
    table,
    event = 'INSERT',
    filter,
    enabled = true,
    maxItems = 100,
  } = options;

  const [data, setData] = useState<T[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const channelRef = useRef<RealtimeChannel | null>(null);
  const supabase = useMemo(() => getSupabaseClient(), []);

  useEffect(() => {
    if (!enabled) {
      return;
    }
    if (!supabase) {
      setError('Supabase client is not configured.');
      return;
    }

    const channel = supabase.channel(channelName);
    channelRef.current = channel;

    channel
      .on(
        'postgres_changes',
        {
          event,
          schema,
          table,
          filter,
        },
        (payload) => {
          setData((prev) => {
            const next = [...prev, payload.new as T];
            return next.slice(Math.max(next.length - maxItems, 0));
          });
        }
      )
      .subscribe((status) => {
        setIsConnected(status === 'SUBSCRIBED');
        if (status === 'CHANNEL_ERROR') {
          setError(`Realtime channel error on ${channelName}`);
        }
      });

    return () => {
      setIsConnected(false);
      if (channelRef.current) {
        void supabase.removeChannel(channelRef.current);
        channelRef.current = null;
      }
    };
  }, [channelName, enabled, event, filter, maxItems, schema, supabase, table]);

  return { data, isConnected, error };
}
