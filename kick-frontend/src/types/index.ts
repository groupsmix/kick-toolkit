/** Kick user profile returned from the OAuth flow. */
export interface KickUser {
  user_id: number;
  name: string;
  email: string | null;
  profile_picture: string | null;
  bio: string | null;
  streamer_channel: string | null;
}

/** Dashboard aggregate statistics from the API. */
export interface DashboardStats {
  total_messages: number;
  flagged_messages: number;
  unique_users: number;
  active_giveaways: number;
  active_tournaments: number;
  flagged_accounts: number;
  total_commands: number;
  moderation_rate: number;
}
