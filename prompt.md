```javascript
"use client"

import type React from "react"

import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Textarea } from "@/components/ui/textarea"
import { getAuthHeader } from "@/lib/auth"
import { BASE_URL } from "@/lib/host"
import { cn } from "@/lib/utils"
import { AnimatePresence, motion } from "framer-motion"
import { BriefcaseBusiness, CheckCircle2, ChevronLeft, ChevronRight, Code2, GitBranch, Github, Gitlab, Globe, GraduationCap, Linkedin, MapPin, Plus, Terminal, Trash2, Twitter, User } from 'lucide-react'
import { useEffect, useRef, useState } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar"
import { Badge } from "./ui/badge"

interface ProfileOnboardingProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onComplete: (data: any) => void
    initialData?: any
}

export function ProfileOnboarding({ open, onOpenChange, onComplete, initialData = {} }: ProfileOnboardingProps) {
    const [step, setStep] = useState(1)
    const [formData, setFormData] = useState({
        name: initialData.name ?? "",
        bio: initialData.bio ?? "",
        location: initialData.location ?? "",
        website: initialData.website ?? "",
        avatar: initialData.avatar ?? "/placeholder.svg?height=150&width=150",
        coverImage: initialData.coverImage ?? "/placeholder.svg?height=400&width=1200",
        github: initialData.github ?? "",
        gitlab: initialData.gitlab ?? "",
        twitter: initialData.twitter ?? "",
        linkedin: initialData.linkedin ?? "",
        skills: initialData.skills ?? [],
        user_projects: initialData.user_projects ?? [],
        education: initialData.education ?? [],
        experience: initialData.experience ?? [],
    })

    const [availableSkills, setAvailableSkills] = useState<any[]>([])
    const [isLoadingSkills, setIsLoadingSkills] = useState(false)

    const [newSkill, setNewSkill] = useState({
        name: "",
        slug: "",
        description: "",
        skill_type: null,
        icon: "",
        parent: null,
        related_skills: [],
        level: 50, // Default skill level
        id: "",
    })

    useEffect(() => {
        if (step === 4) {
            fetchSkills()
        }
    }, [step])

    const [newProject, setNewProject] = useState({
        name: "",
        description: "",
        link: "",
        language: "",
        image: "/placeholder.svg?height=200&width=400",
    })

    const fileInputRef = useRef<HTMLInputElement>(null)

    const totalSteps = 5

    // Update formData when initialData changes
    useEffect(() => {
        setFormData({
            name: initialData.name ?? "",
            bio: initialData.bio ?? "",
            location: initialData.location ?? "",
            website: initialData.website ?? "",
            avatar: initialData.avatar ?? "/placeholder.svg?height=150&width=150",
            coverImage: initialData.coverImage ?? "/placeholder.svg?height=400&width=1200",
            github: initialData.github ?? "",
            gitlab: initialData.gitlab ?? "",
            twitter: initialData.twitter ?? "",
            linkedin: initialData.linkedin ?? "",
            skills: initialData.skills ?? [],
            user_projects: initialData.user_projects ?? [],
            education: initialData.education ?? [],
            experience: initialData.experience ?? [],
        })
    }, [initialData])

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target
        setFormData((prev) => ({ ...prev, [name]: value }))
    }

    const fetchSkills = async () => {
        try {
            setIsLoadingSkills(true)
            const response = await fetch(`${BASE_URL}/api/core/skills/`, {
                headers: {
                    ...(await getAuthHeader()),
                },
            })

            if (response.ok) {
                const data = await response.json()
                if (Array.isArray(data)) {
                    setAvailableSkills(data)
                } else if (data?.results?.length) {
                    setAvailableSkills(data.results)
                } else {
                    console.error("Invalid skills data structure")
                    setAvailableSkills([])
                }
            } else {
                console.error("Failed to fetch skills")
                setAvailableSkills([])
            }
        } catch (error) {
            console.error("Error fetching skills:", error)
            setAvailableSkills([])
        } finally {
            setIsLoadingSkills(false)
        }
    }

    const handleSkillChange = (skillId: string) => {
        const selectedSkill = availableSkills.find((skill) => skill.id === skillId)
        if (selectedSkill) {
            setNewSkill((prev) => ({
                ...selectedSkill,
                level: 50, // Reset level when selecting new skill
                id: selectedSkill.id,
            }))
        }
    }

    const handleSkillLevelChange = (value: number[]) => {
        setNewSkill((prev) => ({ ...prev, level: value[0] }))
    }

    const handleAddSkill = () => {
        if (!newSkill.id) return

        // Check if skill already exists by ID
        const skillExists = formData.skills.some((skill: any) => skill.id === newSkill.id)
        if (skillExists) return

        setFormData((prev) => ({
            ...prev,
            skills: [
                ...prev.skills,
                {
                    ...newSkill,
                    user_level: newSkill.level,
                },
            ],
        }))

        setNewSkill({
            name: "",
            slug: "",
            description: "",
            skill_type: null,
            icon: "",
            parent: null,
            related_skills: [],
            level: 50,
            id: "",
        })
    }

    const handleRemoveSkill = (index: number) => {
        setFormData((prev) => ({
            ...prev,
            skills: prev.skills.filter((_: any, i: number) => i !== index),
        }))
    }

    const handleProjectChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target
        setNewProject((prev) => ({ ...prev, [name]: value }))
    }

    const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            const imageUrl = URL.createObjectURL(file)
            setNewProject((prev) => ({ ...prev, image: imageUrl }))
            // Reset file input to allow same file re-upload
            if (fileInputRef.current) fileInputRef.current.value = ""
        }
    }

    const handleAddProject = () => {
        if (newProject.name.trim() === "" || newProject.description.trim() === "") return

        setFormData((prev) => ({
            ...prev,
            user_projects: [
                ...prev.user_projects,
                {
                    ...newProject,
                    id: Date.now(),
                    stars: Math.floor(Math.random() * 300) + 50,
                    forks: Math.floor(Math.random() * 100) + 10,
                },
            ],
        }))

        setNewProject({
            name: "",
            description: "",
            link: "",
            language: "",
            image: "/placeholder.svg?height=200&width=400",
        })
    }

    const handleRemoveProject = (index: number) => {
        setFormData((prev) => ({
            ...prev,
            user_projects: prev.user_projects.filter((_: any, i: number) => i !== index),
        }))
    }

    // ... Rest of the code remains the same until getStepDescription

    const getStepDescription = (stepNumber: number) => {
        switch (stepNumber) {
            case 1:
                return "Let's start with your basic profile information"
            case 2:
                return "Where are you located and how can people reach you?"
            case 3:
                return "Connect your social and developer accounts"
            case 4:
                return "What technologies and skills do you have?"
            case 5:
                return "Showcase your projects and contributions" // Fixed typo here
            default:
                return "Complete your profile to get the most out of Hackitech"
        }
    }

    // ... Rest of the component remains the same except for key props in lists

    {/* In skills list rendering */}
    {formData.skills.map((skill: any) => (
        <div key={skill.id} className="bg-white/5 rounded-lg p-3 flex items-center justify-between">
            {/* ... skill content ... */}
        </div>
    ))}

    {/* In projects list rendering */}
    {formData.user_projects.map((project: any) => (
        <div key={project.id} className="bg-white/5 rounded-lg p-3 flex flex-col">
            {/* ... project content ... */}
        </div>
    ))}
}
```
