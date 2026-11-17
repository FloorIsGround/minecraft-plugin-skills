import java.util.ArrayList;
import java.util.List;

/** Fictional plain-Java lifecycle model; no server or network is exercised. */
public final class TokenExchange {
    static final class Clock {
        final List<Runnable> pending = new ArrayList<>();
        void nextTick(Runnable task) { pending.add(task); }
        void advance() {
            var ready = new ArrayList<>(pending);
            pending.clear();
            ready.forEach(Runnable::run);
        }
    }

    static final class State {
        final int initial;
        int carried, stored, badges;
        boolean online = true;
        boolean open = true;
        State(int tokens) { initial = tokens; carried = tokens; }
        void close() { stored += carried; carried = 0; open = false; }
        int accountedTokens() { return carried + stored + 2 * badges; }
    }

    static boolean redeem(State state, Clock clock) {
        if (!state.online || !state.open || state.carried < 2) return false;
        state.badges++;
        int remainder = state.carried - 2;
        clock.nextTick(() -> {
            if (state.online) state.carried = remainder;
        });
        return true;
    }

    static boolean run(String schedule, int tokens) {
        State state = new State(tokens);
        Clock clock = new Clock();
        redeem(state, clock);
        switch (schedule) {
            case "normal" -> { clock.advance(); state.close(); }
            case "close_before_callback" -> {
                state.close(); clock.advance(); state.close();
            }
            case "two_clicks_before_callback" -> {
                redeem(state, clock); clock.advance(); state.close();
            }
            case "disconnect_before_callback" -> {
                state.close(); state.online = false; clock.advance();
            }
            default -> throw new IllegalArgumentException(schedule);
        }
        boolean conserved = state.accountedTokens() == state.initial;
        int expectedBadges = tokens < 2 ? 0
            : schedule.equals("two_clicks_before_callback") ? Math.min(2, tokens / 2) : 1;
        boolean outputCount = state.badges == expectedBadges;
        System.out.printf(
            "{\"case\":\"%s/%d\",\"observations\":{\"initial\":%d,\"stored\":%d,\"carried\":%d,\"badges\":%d},"
            + "\"assertions\":{\"tokens_conserved\":%s,\"output_count\":%s}}%n",
            schedule, tokens, tokens, state.stored, state.carried, state.badges,
            conserved, outputCount);
        return conserved && outputCount;
    }

    public static void main(String[] args) {
        boolean passed = true;
        for (int tokens : new int[]{0, 1, 2, 7}) {
            for (String schedule : List.of("normal", "close_before_callback",
                    "two_clicks_before_callback", "disconnect_before_callback")) {
                passed = run(schedule, tokens) && passed;
            }
        }
        if (!passed) System.exit(1);
    }
}
