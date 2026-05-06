// ==================== RESPONSE DTOs ====================

export interface AuthResponseDto {
  token: string;
  user: UserResponseDto;
  expiresAt: string;
}

export interface UserResponseDto {
  id: number;
  fullName: string;
  email: string;
  phone: string;
  city: string;
  role: string;
  profilePhoto?: string;
  createdAt: string;
}

export interface LawyerResponseDto {
  id: number;
  userId: number;
  fullName: string;
  email: string;
  specializations: string[];
  experienceYears: number;
  isVerified: boolean;
  address: string;
  latitude: number;
  longitude: number;
  averageRating: number;
  reviewCount: number;
  createdAt: string;
}

export interface BookingResponseDto {
  id: number;
  userId: number;
  lawyerId: number;
  specializationId: number;
  interactionTypeId: number;
  priceSnapshot: number;
  durationSnapshot: number;
  date: string;
  status: string;
  paymentStatus: string;
  createdAt: string;
  clientName?: string;
  clientEmail?: string;
  clientPhone?: string;
  lawyerName?: string;
  lawyerSpecialization?: string;
}

export interface ReviewResponseDto {
  id: number;
  bookingId: number;
  userId: number;
  lawyerId: number;
  rating: number;
  comment: string;
  createdAt: string;
  userName?: string;
  lawyerName?: string;
}

export interface NotificationResponseDto {
  id: number;
  userId: number;
  title: string;
  message: string;
  type: string;
  isRead: boolean;
  createdAt: string;
}

export interface PaymentSessionResponseDto {
  id: number;
  bookingId: number;
  amount: number;
  status: string;
  provider: string;
  providerSessionId: string;
  checkoutUrl?: string;
  createdAt: string;
}

export interface ChatRoomResponseDto {
  id: number;
  bookingId: number;
  isArchived: boolean;
  createdAt: string;
  messageCount: number;
}

export interface ChatMessageResponseDto {
  id: number;
  chatRoomId: number;
  senderId: number;
  senderName: string;
  message: string;
  sentAt: string;
}

export interface SpecializationDto {
  id: number;
  name: string;
}

export interface InteractionTypeDto {
  id: number;
  name: string;
  description?: string;
}

export interface LawyerPricingDto {
  specializationId: number;
  interactionTypeId: number;
  price: number;
  durationMinutes: number;
}

// ==================== REQUEST DTOs ====================

export interface LoginDto {
  email: string;
  password: string;
}

export interface UserRegisterDto {
  fullName: string;
  email: string;
  password: string;
  phone: string;
  city: string;
  role: string;
  adminSecret?: string;
}

export interface LawyerRegisterDto {
  experienceYears: number;
  address: string;
  latitude: number;
  longitude: number;
  specializationIds: number[];
  baseHourlyRate?: number;
}

export interface RegisterRequestDto {
  user: UserRegisterDto;
  lawyer?: LawyerRegisterDto;
}

export interface BookingDto {
  lawyerId: number;
  date: string;
  userId?: number;
  specializationId: number;
  interactionTypeId: number;
}

export interface ReviewCreateDto {
  bookingId: number;
  lawyerId: number;
  rating: number;
  comment: string;
}

export interface PaymentDto {
  bookingId: number;
  amount: number;
}
