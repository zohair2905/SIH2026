"use client";

import { useState } from "react";
import {
  Activity,
  Eye,
  Search,
  ShieldCheck,
  UserPlus,
  Users as UsersIcon,
} from "lucide-react";
import { toast } from "sonner";

import { PageHeading } from "@/components/layout/page-heading";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { initialUsers } from "@/mocks/users";
import type { PlatformUser } from "@/types";

export default function UsersPage() {
  const [users, setUsers] = useState(initialUsers);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<PlatformUser | null>(null);

  const [newUser, setNewUser] = useState({
    name: "",
    role: "Investigator",
    department: "",
    email: "",
  });

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.name.toLowerCase().includes(search.toLowerCase()) ||
      user.email.toLowerCase().includes(search.toLowerCase()) ||
      user.department.toLowerCase().includes(search.toLowerCase());

    const matchesRole = roleFilter === "All" || user.role === roleFilter;
    const matchesStatus =
      statusFilter === "All" || user.status === statusFilter;

    return matchesSearch && matchesRole && matchesStatus;
  });

  const addUser = () => {
    if (!newUser.name || !newUser.email || !newUser.department) {
      toast.error("Fill in name, department and email.");
      return;
    }

    const user: PlatformUser = {
      id: users.length + 1,
      name: newUser.name,
      role: newUser.role,
      department: newUser.department,
      email: newUser.email,
      status: "Active",
      lastLogin: "Never",
    };

    setUsers([...users, user]);
    setNewUser({ name: "", role: "Investigator", department: "", email: "" });
    setShowAddModal(false);
    toast.success("User created successfully");
  };

  return (
    <div className="space-y-6">
      <PageHeading
        title="Users"
        description="Manage authorized users and access permissions"
      >
        <span>Last updated: 16 Sep 2026, 15:30</span>
      </PageHeading>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            icon: UsersIcon,
            iconBg: "bg-accent text-primary",
            label: "Total Users",
            value: users.length,
            note: "Registered",
          },
          {
            icon: ShieldCheck,
            iconBg: "bg-green-100 text-green-700",
            label: "Active Users",
            value: users.filter((u) => u.status === "Active").length,
            note: "Authorized",
          },
          {
            icon: Activity,
            iconBg: "bg-orange-100 text-orange-700",
            label: "Investigators",
            value: users.filter((u) => u.role === "Investigator").length,
            note: "Field access",
          },
          {
            icon: UsersIcon,
            iconBg: "bg-purple-100 text-purple-700",
            label: "Analysts",
            value: users.filter((u) => u.role === "Analyst").length,
            note: "Intelligence access",
          },
        ].map(({ icon: Icon, iconBg, label, value, note }) => (
          <div
            key={label}
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm"
          >
            <div
              className={`flex size-10 items-center justify-center rounded-md ${iconBg}`}
            >
              <Icon className="size-5" />
            </div>
            <div>
              <span className="block text-xs text-muted-foreground">
                {label}
              </span>
              <strong className="block text-xl text-foreground">{value}</strong>
              <small className="block text-xs text-muted-foreground">
                {note}
              </small>
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="w-64 pl-9"
            placeholder="Search users..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
        >
          <option value="All">All Roles</option>
          <option value="Administrator">Administrator</option>
          <option value="Investigator">Investigator</option>
          <option value="Analyst">Analyst</option>
        </select>

        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="All">All Status</option>
          <option value="Active">Active</option>
          <option value="Inactive">Inactive</option>
        </select>

        <Button onClick={() => setShowAddModal(true)}>
          <UserPlus className="size-4" /> Add New User
        </Button>
      </div>

      <Panel icon={UsersIcon} title="Platform Users">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                <th className="px-5 py-3">User</th>
                <th className="px-5 py-3">Role</th>
                <th className="px-5 py-3">Department</th>
                <th className="px-5 py-3">Email</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Last Login</th>
                <th className="px-5 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user) => (
                <tr
                  key={user.id}
                  className="border-b border-border last:border-0 hover:bg-muted/50"
                >
                  <td className="px-5 py-3 font-semibold text-foreground">
                    {user.name}
                  </td>
                  <td className="px-5 py-3">
                    <span className="rounded bg-secondary px-2 py-1 text-xs font-semibold text-primary">
                      {user.role}
                    </span>
                  </td>
                  <td className="px-5 py-3">{user.department}</td>
                  <td className="px-5 py-3">{user.email}</td>
                  <td className="px-5 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                        user.status === "Active"
                          ? "bg-green-100 text-green-700"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {user.status}
                    </span>
                  </td>
                  <td className="px-5 py-3">{user.lastLogin}</td>
                  <td className="px-5 py-3">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedUser(user)}
                    >
                      <Eye className="size-3.5" /> View
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New User</DialogTitle>
            <DialogDescription>
              Create an authorized platform account.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            <Input
              placeholder="Full Name"
              value={newUser.name}
              onChange={(e) =>
                setNewUser((p) => ({ ...p, name: e.target.value }))
              }
            />
            <select
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={newUser.role}
              onChange={(e) =>
                setNewUser((p) => ({ ...p, role: e.target.value }))
              }
            >
              <option>Investigator</option>
              <option>Analyst</option>
              <option>Administrator</option>
            </select>
            <Input
              placeholder="Department"
              value={newUser.department}
              onChange={(e) =>
                setNewUser((p) => ({ ...p, department: e.target.value }))
              }
            />
            <Input
              placeholder="Official Email"
              type="email"
              value={newUser.email}
              onChange={(e) =>
                setNewUser((p) => ({ ...p, email: e.target.value }))
              }
            />
            <Button className="w-full" onClick={addUser}>
              Create User
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog
        open={selectedUser !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedUser(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>User Details</DialogTitle>
          </DialogHeader>
          {selectedUser && (
            <div>
              {(
                [
                  ["Name", selectedUser.name],
                  ["Role", selectedUser.role],
                  ["Department", selectedUser.department],
                  ["Email", selectedUser.email],
                  ["Status", selectedUser.status],
                  ["Last Login", selectedUser.lastLogin],
                ] as const
              ).map(([label, value]) => (
                <div
                  key={label}
                  className="flex items-center justify-between border-b border-border py-2.5 last:border-0"
                >
                  <span className="text-sm text-muted-foreground">
                    {label}
                  </span>
                  <strong className="text-sm text-foreground">{value}</strong>
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}