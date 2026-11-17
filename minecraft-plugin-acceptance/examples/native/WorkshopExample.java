package example.workshop;

import com.google.gson.GsonBuilder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.bukkit.Bukkit;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.ConsoleCommandSender;
import org.bukkit.entity.Player;
import org.bukkit.event.Cancellable;
import org.bukkit.event.Event;
import org.bukkit.event.EventHandler;
import org.bukkit.event.HandlerList;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.permissions.PermissionAttachment;
import org.bukkit.plugin.java.JavaPlugin;

/** Fictional feature and test fixture for a disposable local server only. */
public final class WorkshopExample extends JavaPlugin implements Listener {
    private final Map<UUID, PermissionAttachment> permissions = new LinkedHashMap<>();
    private final Map<UUID, Integer> issued = new LinkedHashMap<>();
    private final List<Map<String, Object>> assertions = new ArrayList<>();
    private int processed, claimEvents, cancelledEvents;
    private boolean cancelClaims;
    private String stage = "joining";
    private final int expected = Integer.getInteger("workshop.players", 4);

    public static final class ClaimEvent extends Event implements Cancellable {
        private static final HandlerList HANDLERS = new HandlerList();
        private boolean cancelled;
        public boolean isCancelled() { return cancelled; }
        public void setCancelled(boolean value) { cancelled = value; }
        public HandlerList getHandlers() { return HANDLERS; }
        public static HandlerList getHandlerList() { return HANDLERS; }
    }

    @Override public void onEnable() {
        Bukkit.getPluginManager().registerEvents(this, this);
        save("phase.json", Map.of("stage", stage));
    }

    @EventHandler public void join(PlayerJoinEvent event) {
        Player player = event.getPlayer();
        if (!player.getName().matches("Workshop[0-9]{3,5}")) return;
        player.setOp(index(player) % 4 == 3);
        PermissionAttachment attachment = player.addAttachment(this);
        attachment.setPermission("workshop.claim", initialAllowed(player));
        attachment.setPermission("workshop.inspect", index(player) % 4 == 2);
        permissions.put(player.getUniqueId(), attachment);
        issued.put(player.getUniqueId(), 0);
        state();
    }

    @EventHandler public void cancellation(ClaimEvent event) {
        claimEvents++;
        if (cancelClaims) { event.setCancelled(true); cancelledEvents++; }
    }

    private int index(Player player) { return Integer.parseInt(player.getName().substring(8)); }
    private boolean initialAllowed(Player player) { return index(player) % 4 == 1; }
    private List<Player> players() {
        return Bukkit.getOnlinePlayers().stream()
            .filter(p -> permissions.containsKey(p.getUniqueId()))
            .map(p -> (Player) p)
            .sorted(java.util.Comparator.comparing(Player::getName)).toList();
    }
    private void check(String name, boolean passed) {
        assertions.add(Map.of("name", name, "passed", passed));
    }
    private void save(String name, Object value) {
        try {
            Files.createDirectories(getDataFolder().toPath());
            Path target = getDataFolder().toPath().resolve(name);
            Path temporary = target.resolveSibling(name + ".tmp");
            Files.writeString(temporary, new GsonBuilder().setPrettyPrinting().create().toJson(value));
            Files.move(temporary, target, StandardCopyOption.REPLACE_EXISTING);
        } catch (Exception error) { throw new IllegalStateException(error); }
    }
    private void state() {
        save("state.json", Map.of("online", players().size(), "processed", processed, "stage", stage));
    }
    private void finish(String error) {
        Map<String, Object> report = new LinkedHashMap<>();
        boolean passed = error == null && !assertions.isEmpty()
            && assertions.stream().allMatch(row -> Boolean.TRUE.equals(row.get("passed")));
        report.put("status", passed ? "PASS" : "FAIL");
        report.put("evidence_level", "native Paper players and network-issued commands");
        report.put("assertions", assertions);
        report.put("observations", Map.of("online", players().size(), "commands_processed", processed,
            "claim_events", claimEvents, "cancelled_events", cancelledEvents,
            "server", Bukkit.getVersion(), "java", System.getProperty("java.version"),
            "synthetic_permission_attachments", true, "external_permission_provider", false));
        if (error != null) report.put("fixture_error", error);
        save("result.json", report);
    }

    @Override public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (command.getName().equals("workshop")) {
            if (!(sender instanceof Player player) || !permissions.containsKey(player.getUniqueId())) return true;
            if (args.length != 1 || !args[0].equals("claim")) return true;
            if (player.hasPermission("workshop.claim")) {
                ClaimEvent event = new ClaimEvent();
                Bukkit.getPluginManager().callEvent(event);
                if (!event.isCancelled()) issued.compute(player.getUniqueId(), (key, old) -> old + 1);
            }
            processed++;
            state();
            return true;
        }
        if (!(sender instanceof ConsoleCommandSender) || args.length != 1) return true;
        try {
            List<Player> people = players();
            if (people.size() != expected) throw new IllegalStateException("Expected connected fixture players");
            String action = args[0];
            if (action.equals("prepare")) {
                if (!stage.equals("joining")) throw new IllegalStateException("Unexpected prepare");
                check("expected_players_connected", people.size() == expected);
                stage = "initial";
            } else {
                if (!action.equals("verify_" + stage)) throw new IllegalStateException("Unexpected test stage");
                int stageIndex = List.of("initial", "revoked", "granted", "cancelled").indexOf(stage);
                check(stage + "/processed", processed == expected * (stageIndex + 1));
                for (Player player : people) {
                    int wanted = (initialAllowed(player) ? 1 : 0) + (stageIndex >= 2 ? 1 : 0);
                    check(stage + "/effect/" + player.getName(), issued.get(player.getUniqueId()) == wanted);
                    boolean allowed = stageIndex >= 2 || (stageIndex == 0 && initialAllowed(player));
                    check(stage + "/permission/" + player.getName(), player.hasPermission("workshop.claim") == allowed);
                }
                if (stage.equals("initial")) {
                    permissions.values().forEach(a -> a.setPermission("workshop.claim", false));
                    stage = "revoked";
                } else if (stage.equals("revoked")) {
                    permissions.values().forEach(a -> a.setPermission("workshop.claim", true));
                    stage = "granted";
                } else if (stage.equals("granted")) {
                    cancelClaims = true;
                    stage = "cancelled";
                } else {
                    check("cancelled_event_count", cancelledEvents == expected);
                    stage = "complete";
                    finish(null);
                }
            }
            save("phase.json", Map.of("stage", stage));
            state();
        } catch (Throwable error) { finish(error.toString()); }
        return true;
    }
}
