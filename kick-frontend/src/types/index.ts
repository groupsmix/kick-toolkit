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

/** Marketplace seller profile. */
export interface SellerProfile {
  id: string;
  user_id: string;
  display_name: string;
  bio: string;
  avatar_url: string | null;
  website: string | null;
  total_sales: number;
  total_revenue: number;
  rating_avg: number;
  rating_count: number;
  status: string;
  created_at: string;
  updated_at: string;
}

/** Marketplace item listing. */
export interface MarketplaceItem {
  id: string;
  seller_id: string;
  title: string;
  description: string;
  category: string;
  price: number;
  currency: string;
  preview_url: string | null;
  download_url: string | null;
  thumbnail_url: string | null;
  tags: string[];
  status: string;
  download_count: number;
  rating_avg: number;
  rating_count: number;
  created_at: string;
  updated_at: string;
}

/** Marketplace purchase record. */
export interface MarketplacePurchase {
  id: string;
  item_id: string;
  buyer_user_id: string;
  seller_id: string;
  price_paid: number;
  platform_fee: number;
  seller_payout: number;
  status: string;
  payment_reference: string | null;
  created_at: string;
  title?: string;
  category?: string;
  thumbnail_url?: string | null;
  download_url?: string | null;
}

/** Marketplace review. */
export interface MarketplaceReview {
  id: string;
  item_id: string;
  user_id: string;
  rating: number;
  comment: string;
  created_at: string;
  updated_at: string;
}

/** Seller revenue analytics. */
export interface SellerRevenueAnalytics {
  seller_id: string;
  total_revenue: number;
  total_sales: number;
  platform_fees: number;
  net_revenue: number;
  pending_payout: number;
  items_listed: number;
  avg_item_rating: number;
  monthly_revenue: Array<{ month: string; revenue: number }>;
  top_items: Array<{
    id: string;
    title: string;
    category: string;
    price: number;
    download_count: number;
    rating_avg: number;
  }>;
}
