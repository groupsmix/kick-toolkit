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

/** Subscription plan definition. */
export interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  currency: string;
  interval: string;
  features: string[];
  limits: Record<string, number>;
}

/** User subscription data from the API. */
export interface SubscriptionData {
  id: string;
  user_id: string;
  plan: string;
  status: string;
  lemon_subscription_id: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  created_at: string;
  updated_at: string;
}

/** Subscription + usage response from /api/subscription/me. */
export interface SubscriptionResponse {
  subscription: SubscriptionData;
  plan: SubscriptionPlan;
  usage: Record<string, number>;
}
