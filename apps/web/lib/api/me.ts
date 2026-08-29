import { apiClient } from './client';
import { CitizenProfile, CitizenProfileUpdate, Address, AddressInput } from '@/types/api';

export async function getProfile(): Promise<CitizenProfile> {
  return apiClient<CitizenProfile>('/me');
}

export async function updateProfile(data: CitizenProfileUpdate): Promise<CitizenProfile> {
  return apiClient<CitizenProfile>('/me', {
    method: 'PATCH',
    body: data
  });
}

export async function getAccount(): Promise<any> {
  return apiClient('/me/account');
}

export async function getAddresses(): Promise<Address[]> {
  return apiClient<Address[]>('/me/addresses');
}

export async function addAddress(data: AddressInput): Promise<Address> {
  return apiClient<Address>('/me/addresses', {
    method: 'POST',
    body: data
  });
}

export async function updateAddress(addressId: string, data: AddressInput): Promise<Address> {
  return apiClient<Address>(`/me/addresses/${addressId}`, {
    method: 'PUT',
    body: data
  });
}

export async function deleteAddress(addressId: string): Promise<void> {
  await apiClient(`/me/addresses/${addressId}`, {
    method: 'DELETE'
  });
}
