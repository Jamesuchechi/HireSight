export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          updated_at: string
          full_name: string | null
          role: 'candidate' | 'recruiter'
          avatar_url: string | null
          cover_url: string | null
          bio: string | null
          onboarding_completed: boolean
          headline: string | null
          location: string | null
          phone: string | null
          skills: Json | null
          experience: Json | null
          education: Json | null
          certifications: Json | null
          portfolio_links: Json | null
          job_preferences: Json | null
          company_data: Json | null
        }
        Insert: {
          id: string
          updated_at?: string
          full_name?: string | null
          role?: 'candidate' | 'recruiter'
          avatar_url?: string | null
          cover_url?: string | null
          bio?: string | null
          onboarding_completed?: boolean
          headline?: string | null
          location?: string | null
          phone?: string | null
          skills?: Json | null
          experience?: Json | null
          education?: Json | null
          certifications?: Json | null
          portfolio_links?: Json | null
          job_preferences?: Json | null
          company_data?: Json | null
        }
        Update: {
          id?: string
          updated_at?: string
          full_name?: string | null
          role?: 'candidate' | 'recruiter'
          avatar_url?: string | null
          cover_url?: string | null
          bio?: string | null
          onboarding_completed?: boolean
          headline?: string | null
          location?: string | null
          phone?: string | null
          skills?: Json | null
          experience?: Json | null
          education?: Json | null
          certifications?: Json | null
          portfolio_links?: Json | null
          job_preferences?: Json | null
          company_data?: Json | null
        }
      }
      resumes: {
        Row: {
          id: string
          user_id: string
          title: string
          file_url: string
          status: 'uploaded' | 'parsing' | 'parsed' | 'failed'
          is_primary: boolean
          parsed_content: Json | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          title: string
          file_url: string
          status?: 'uploaded' | 'parsing' | 'parsed' | 'failed'
          is_primary?: boolean
          parsed_content?: Json | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          title?: string
          file_url?: string
          status?: 'uploaded' | 'parsing' | 'parsed' | 'failed'
          is_primary?: boolean
          parsed_content?: Json | null
          created_at?: string
          updated_at?: string
        }
      }
      jobs: {
        Row: {
          id: string
          company_id: string
          title: string
          description: string
          requirements: string | null
          salary_min: number | null
          salary_max: number | null
          currency: string
          location: string | null
          location_coords: string | null
          remote_type: 'remote' | 'hybrid' | 'onsite'
          experience_level: 'entry' | 'mid' | 'senior' | 'lead' | 'executive'
          job_type: 'full-time' | 'part-time' | 'contract' | 'internship'
          status: 'draft' | 'active' | 'closed' | 'deleted'
          expires_at: string | null
          created_at: string
          updated_at: string
          responsibilities: string | null
          nice_to_have: string | null
          benefits: string | null
          department: string | null
          salary_period: 'hourly' | 'monthly' | 'yearly'
          positions_available: number
          application_deadline: string | null
          requires_cover_letter: boolean
          requires_portfolio: boolean
          is_featured: boolean
        }
        Insert: {
          id?: string
          company_id: string
          title: string
          description: string
          requirements?: string | null
          salary_min?: number | null
          salary_max?: number | null
          currency?: string
          location?: string | null
          location_coords?: string | null
          remote_type: 'remote' | 'hybrid' | 'onsite'
          experience_level: 'entry' | 'mid' | 'senior' | 'lead' | 'executive'
          job_type: 'full-time' | 'part-time' | 'contract' | 'internship'
          status?: 'draft' | 'active' | 'closed' | 'deleted'
          expires_at?: string | null
          created_at?: string
          updated_at?: string
          responsibilities?: string | null
          nice_to_have?: string | null
          benefits?: string | null
          department?: string | null
          salary_period?: 'hourly' | 'monthly' | 'yearly'
          positions_available?: number
          application_deadline?: string | null
          requires_cover_letter?: boolean
          requires_portfolio?: boolean
          is_featured?: boolean
        }
        Update: {
          id?: string
          company_id?: string
          title?: string
          description?: string
          requirements?: string | null
          salary_min?: number | null
          salary_max?: number | null
          currency?: string
          location?: string | null
          location_coords?: string | null
          remote_type?: 'remote' | 'hybrid' | 'onsite'
          experience_level?: 'entry' | 'mid' | 'senior' | 'lead' | 'executive'
          job_type?: 'full-time' | 'part-time' | 'contract' | 'internship'
          status?: 'draft' | 'active' | 'closed' | 'deleted'
          expires_at?: string | null
          created_at?: string
          updated_at?: string
          responsibilities?: string | null
          nice_to_have?: string | null
          benefits?: string | null
          department?: string | null
          salary_period?: 'hourly' | 'monthly' | 'yearly'
          positions_available?: number
          application_deadline?: string | null
          requires_cover_letter?: boolean
          requires_portfolio?: boolean
          is_featured?: boolean
        }
      }
      job_skills: {
        Row: {
          id: string
          job_id: string
          skill_name: string
          is_required: boolean
          created_at: string
        }
        Insert: {
          id?: string
          job_id: string
          skill_name: string
          is_required?: boolean
          created_at?: string
        }
        Update: {
          id?: string
          job_id?: string
          skill_name?: string
          is_required?: boolean
          created_at?: string
        }
      }
      job_screening_questions: {
        Row: {
          id: string
          job_id: string
          question: string
          input_type: 'short_text' | 'long_text' | 'yes_no' | 'multiple_choice'
          options: Json | null
          is_required: boolean
          order_index: number
        }
        Insert: {
          id?: string
          job_id: string
          question: string
          input_type: 'short_text' | 'long_text' | 'yes_no' | 'multiple_choice'
          options?: Json | null
          is_required?: boolean
          order_index?: number
        }
        Update: {
          id?: string
          job_id?: string
          question?: string
          input_type?: 'short_text' | 'long_text' | 'yes_no' | 'multiple_choice'
          options?: Json | null
          is_required?: boolean
          order_index?: number
        }
      }
      job_applications: {
        Row: {
          id: string
          job_id: string
          candidate_id: string
          resume_id: string | null
          answers: Json | null
          status: 'applied' | 'screening' | 'interview' | 'offer' | 'hired' | 'rejected'
          match_score: number | null
          source: string | null
          cover_letter: string | null
          notes: string | null
          rating: number | null
          rejection_reason: string | null
          feedback: string | null
          created_at: string
          updated_at: string
          viewed_at: string | null
          is_shortlisted: boolean
          recruiter_rating: number | null
          match_details: Json
          rejection_feedback: Json
          hired_at: string | null
          rejected_at: string | null
          withdrawn_at: string | null
        }
        Insert: {
          id?: string
          job_id: string
          candidate_id: string
          resume_id?: string | null
          answers?: Json | null
          status?: 'applied' | 'screening' | 'interview' | 'offer' | 'hired' | 'rejected'
          match_score?: number | null
          source?: string | null
          cover_letter?: string | null
          notes?: string | null
          rating?: number | null
          rejection_reason?: string | null
          feedback?: string | null
          created_at?: string
          updated_at?: string
          viewed_at?: string | null
          is_shortlisted?: boolean
          recruiter_rating?: number | null
          match_details?: Json
          rejection_feedback?: Json
          hired_at?: string | null
          rejected_at?: string | null
          withdrawn_at?: string | null
        }
        Update: {
          id?: string
          job_id?: string
          candidate_id?: string
          resume_id?: string | null
          answers?: Json | null
          status?: 'applied' | 'screening' | 'interview' | 'offer' | 'hired' | 'rejected'
          match_score?: number | null
          source?: string | null
          cover_letter?: string | null
          notes?: string | null
          rating?: number | null
          rejection_reason?: string | null
          feedback?: string | null
          created_at?: string
          updated_at?: string
          viewed_at?: string | null
          is_shortlisted?: boolean
          recruiter_rating?: number | null
          match_details?: Json
          rejection_feedback?: Json
          hired_at?: string | null
          rejected_at?: string | null
          withdrawn_at?: string | null
        }
      }
      application_notes: {
        Row: {
          id: string
          application_id: string
          author_id: string
          content: string
          is_important: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          application_id: string
          author_id: string
          content: string
          is_important?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          application_id?: string
          author_id?: string
          content?: string
          is_important?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      application_status_history: {
        Row: {
          id: string
          application_id: string
          old_status: string | null
          new_status: string
          changed_by: string | null
          reason: string | null
          created_at: string
        }
        Insert: {
          id?: string
          application_id: string
          old_status?: string | null
          new_status: string
          changed_by?: string | null
          reason?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          application_id?: string
          old_status?: string | null
          new_status?: string
          changed_by?: string | null
          reason?: string | null
          created_at?: string
        }
      }
      saved_jobs: {
        Row: {
          id: string
          job_id: string
          user_id: string
          created_at: string
        }
        Insert: {
          id?: string
          job_id: string
          user_id: string
          created_at?: string
        }
        Update: {
          id?: string
          job_id?: string
          user_id?: string
          created_at?: string
        }
      }
      job_views: {
        Row: {
          id: string
          job_id: string
          user_id: string | null
          viewer_ip: string | null
          user_agent: string | null
          created_at: string
        }
        Insert: {
          id?: string
          job_id: string
          user_id?: string | null
          viewer_ip?: string | null
          user_agent?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          job_id?: string
          user_id?: string | null
          viewer_ip?: string | null
          user_agent?: string | null
          created_at?: string
        }
      }
      saved_searches: {
        Row: {
          id: string
          user_id: string
          name: string
          filters: Json
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          filters: Json
          created_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          filters?: Json
          created_at?: string
        }
      }
      profile_views: {
        Row: {
          id: string
          profile_id: string
          viewer_id: string | null
          viewer_ip: string | null
          user_agent: string | null
          created_at: string
        }
        Insert: {
          id?: string
          profile_id: string
          viewer_id?: string | null
          viewer_ip?: string | null
          user_agent?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          profile_id?: string
          viewer_id?: string | null
          viewer_ip?: string | null
          user_agent?: string | null
          created_at?: string
        }
      }
      interviews: {
        Row: {
          id: string
          job_id: string
          candidate_id: string
          interviewer_id: string | null
          start_time: string
          end_time: string
          location: string | null
          type: 'virtual' | 'on-site' | 'phone'
          status: 'scheduled' | 'completed' | 'cancelled' | 'rescheduled'
          notes: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          job_id: string
          candidate_id: string
          interviewer_id?: string | null
          start_time: string
          end_time: string
          location?: string | null
          type?: 'virtual' | 'on-site' | 'phone'
          status?: 'scheduled' | 'completed' | 'cancelled' | 'rescheduled'
          notes?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          job_id?: string
          candidate_id?: string
          interviewer_id?: string | null
          start_time?: string
          end_time?: string
          location?: string | null
          type?: 'virtual' | 'on-site' | 'phone'
          status?: 'scheduled' | 'completed' | 'cancelled' | 'rescheduled'
          notes?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      api_keys: {
        Row: {
          id: string
          user_id: string
          name: string
          key_hash: string
          key_prefix: string
          is_active: boolean
          created_at: string
          last_used_at: string | null
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          key_hash: string
          key_prefix: string
          is_active?: boolean
          created_at?: string
          last_used_at?: string | null
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          key_hash?: string
          key_prefix?: string
          is_active?: boolean
          created_at?: string
          last_used_at?: string | null
        }
      }
      notification_preferences: {
        Row: {
          user_id: string
          frequency: 'instant' | 'daily' | 'weekly' | 'off'
          notify_jobs: boolean
          notify_applications: boolean
          notify_messages: boolean
          notify_views: boolean
          updated_at: string
        }
        Insert: {
          user_id: string
          frequency?: 'instant' | 'daily' | 'weekly' | 'off'
          notify_jobs?: boolean
          notify_applications?: boolean
          notify_messages?: boolean
          notify_views?: boolean
          updated_at?: string
        }
        Update: {
          user_id?: string
          frequency?: 'instant' | 'daily' | 'weekly' | 'off'
          notify_jobs?: boolean
          notify_applications?: boolean
          notify_messages?: boolean
          notify_views?: boolean
          updated_at?: string
        }
      }
    }
  }
}
