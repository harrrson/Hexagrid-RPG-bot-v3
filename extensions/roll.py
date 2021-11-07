import lightbulb
from hikari import Embed
from random import SystemRandom
import re

from typing import Optional, Tuple
from functools import lru_cache


class RollBaseException(Exception):
    pass


class WrongCommandFormula(RollBaseException):
    def __init__(self, command: str):
        self.command = command


class WrongDiceCount(RollBaseException):
    def __init__(self, dice_count: int):
        self.dice_count = dice_count


class WrongDiceSize(RollBaseException):
    def __init__(self, dice_size: int):
        self.dice_size = dice_size


class DivisionByZeroError(RollBaseException):
    pass


class Roll(lightbulb.Plugin):
    _rng = SystemRandom()
    _max_rolls = 20
    _dice_colours = {'green': ['Small Fail', 'Big Success', 'Big Success', 'Big Success'],
                     'lime': ['Fail', 'Success', 'Big Success', 'Big Success'],
                     'yellow': ['Fail', 'Success', 'Success', 'Big Success'],
                     'white': ['Big Fail', 'Fail', 'Success', 'Big Success'],
                     'orange': ['Big Fail', 'Fail', 'Fail', 'Success'],
                     'red': ['Big Fail', 'Big Fail', 'Fail', 'Success'],
                     'black': ['Big Fail', 'Big Fail', 'Big Fail', 'Small Success']
                     }
    _fate_texts = ('Fate is not on your side :thumbsdown:', 'Fate is on your side :thumbsup:')

    def _find_comment(self, text: str) -> str:
        max_len = 50
        splitted = text.split('!', maxsplit=1)
        if len(splitted) == 1:
            return splitted + [""]
        splitted[1] = splitted[1] if len(splitted[1]) < max_len else splitted[1][:max_len - 3] + "..."
        return splitted

    # created as command, not group, because wanted to reuse commands in slash commands
    @lightbulb.command()
    async def roll(self, ctx: lightbulb.Context, reps: Optional[int] = 1, *, args=''):
        if reps < 1 or reps > self._max_rolls:
            await ctx.respond(f'Invalid number of repetitions: {reps}.\nUse number between 1 - {self._max_rolls}.')
            return
        split = self._find_comment(args)
        command = split[0] if len(split) > 0 else 'd10'
        comment = split[1] if len(split) > 1 else ''
        split_command = command.split(maxsplit=5)
        if split_command[0] in self._dice_colours.keys():
            await self._color_roll(ctx, reps, split_command[0], comment)
        elif split_command[0] == 'fate':
            await self._fate_roll(ctx, reps, comment)
        elif split_command[0] == 'duel':
            await self._duel_roll(ctx=ctx, comment=comment,
                                  p1_dice=split_command[1] if len(split_command) > 1 else 'd10',
                                  p2_dice=split_command[2] if len(split_command) > 2 else 'd10',
                                  p1_name=split_command[3] if len(split_command) > 3 else 'Player 1',
                                  p2_name=split_command[4] if len(split_command) > 4 else 'Player 2',
                                  )
        else:
            await self._default_roll(ctx, reps, command, comment)

    async def _color_roll(self, ctx: lightbulb.Context, reps: int, color: str, comment: str):
        embed = Embed(title=f'Roll for {ctx.member.display_name if ctx.guild_id else ctx.author.username}',
                      description=comment,
                      color=[255, 0, 0])
        for i in range(reps):
            embed.add_field(name=f'Roll #{i + 1}', value=self._dice_colours[color][self._rng.randint(0, 3)],
                            inline=True)
        await ctx.respond(embed=embed)

    async def _fate_roll(self, ctx: lightbulb.Context, reps: int, comment: str):
        embed = Embed(title=f'Fate roll for {ctx.member.display_name if ctx.guild_id else ctx.author.username}',
                      description=comment,
                      color=[255, 0, 0])
        for i in range(reps):
            embed.add_field(name=f'Roll #{i + 1}', value=self._fate_texts[self._rng.randint(0, 1)], inline=True)
        await ctx.respond(embed=embed)

    async def _duel_roll(self, ctx: lightbulb.Context, comment: str, p1_dice: str, p2_dice: str, p1_name: str,
                         p2_name: str) -> None:
        try:
            n_rolls1, dice_size1, modifier1, operator1, threshold1 = self._split_dice(p1_dice)
            n_rolls2, dice_size2, modifier2, operator2, threshold2 = self._split_dice(p2_dice)
        except WrongCommandFormula as e:
            await ctx.respond(f'Wrong dice formula: {e.command}')
            return
        except WrongDiceSize as e:
            await ctx.respond(f'Wrong dice size: {e.dice_size}')
            return
        except WrongDiceCount as e:
            await ctx.respond(f'Wrong dice count: {e.dice_count}')
            return
        rolls1, result1 = self._roll_dice(dice_size1, n_rolls1, modifier1, operator1)
        rolls2, result2 = self._roll_dice(dice_size2, n_rolls2, modifier2, operator2)
        embed = Embed(title=f'Duel! {p1_name} vs {p2_name}',
                      description=comment,
                      color=[255, 0, 0])
        embed.add_field(name=f"{p1_name}'s roll", value=result1, inline=True)
        embed.add_field(name=f"{p2_name}'s roll", value=result2, inline=True)
        embed.add_field(name="Winner:",
                        value=p1_name if result1 > result2 else p2_name if result1 < result2 else "Draw!")
        embed.add_field(name="Rolls:", value=f"{p1_name}: {rolls1}\n{p2_name}: {rolls2}")
        await ctx.respond(embed=embed)

    async def _default_roll(self, ctx: lightbulb.Context, reps: int, command: str, comment: str) -> None:
        try:
            n_rolls, dice_size, modifier, operator, threshold = self._split_dice(command)
        except WrongCommandFormula as e:
            await ctx.respond(f'Wrong dice formula: {e.command}')
            return
        except WrongDiceSize as e:
            await ctx.respond(f'Wrong dice size: {e.dice_size}')
            return
        except WrongDiceCount as e:
            await ctx.respond(f'Wrong dice count: {e.dice_count}')
            return
        embed = Embed(title=f'Roll for {ctx.member.display_name if ctx.guild_id else ctx.author.username}',
                      description=comment,
                      color=[255, 0, 0])
        for i in range(reps):
            rolls, result = self._roll_dice(dice_size, n_rolls, modifier, operator)
            embed.add_field(name=f'Roll #{i + 1}: Result {result}', value=f"{rolls}", inline=True)
        await ctx.respond(embed=embed)

    def _roll_dice(self, dice_size: int = 10, n_of_rolls: int = 1, roll_modifier: int = 0,
                   roll_modifier_type: str = '+') -> Tuple[list[int], int]:
        rolls = [self._rng.randint(1, dice_size) for _ in range(n_of_rolls)]
        rolls.sort(reverse=True)
        result = sum(rolls)
        if roll_modifier_type == '+':
            result = result + roll_modifier
        elif roll_modifier_type == '-':
            result = result - roll_modifier
        elif roll_modifier_type == '*':
            result = result * roll_modifier
        elif roll_modifier_type == '/':
            result = result / roll_modifier
        return rolls, result

    @lru_cache()
    def _split_dice(self, cmd: str) -> tuple[int, int, int | float, str, None | float | int]:
        plus_count = cmd.count('+')
        minus_count = cmd.count('-')
        mul_count = cmd.count('*')
        div_count = cmd.count('/')
        if cmd.count('d') != 1 or cmd.count('e') > 1 or (
                plus_count + minus_count + mul_count + div_count) > 1 or re.search(
            '[a-cf-z!@#$%^&(){}[]:~`";=_,.?/|]', cmd):
            raise WrongCommandFormula(cmd)
        n_rolls, dice_size = cmd.split('d')
        # check, if roll count is an integer number, if not, command is wrong
        if n_rolls:
            try:
                n_rolls = int(n_rolls)
            except ValueError:
                raise WrongCommandFormula(cmd)
        else:
            n_rolls = 1
        # check, if roll count is in valid range
        if n_rolls > self._max_rolls or n_rolls < 1:
            raise WrongDiceCount(n_rolls)
        try:
            # if dice size is integer number, work is over
            dice_size = int(dice_size)
            if dice_size < 2:
                raise WrongDiceSize(dice_size)
            modifier = 0
            operator = '+'
            threshold = None
        except ValueError:
            # if not, check if user gives threshold value
            if dice_size.count('e') == 1:
                # if yes, extract it from dice size
                dice_size, threshold = dice_size.split('e')
                # check, if threshold is float number
                try:
                    threshold = float(threshold)
                    if threshold.is_integer():
                        threshold = int(threshold)
                except ValueError:
                    raise WrongCommandFormula(cmd)
            else:
                threshold = None
            # Check again, if dice size is integer number (maybe threshold was problem earlier)
            try:
                dice_size = int(dice_size)
                if dice_size < 2:
                    raise WrongDiceSize(dice_size)
                modifier = 0
                operator = '+'
            except ValueError:
                # If not, that means it can contain modifier
                # only one of below variables can be one, so we got at max one character string
                operator = ('+' * plus_count) + ('-' * minus_count) + ('*' * mul_count) + ('/' * div_count)
                # check, if any math operator was found. If not, rolling formula is wrong
                if not operator:
                    raise WrongCommandFormula
                dice_size, modifier = dice_size.split(operator)
                # Check once again,if dice size is integer number
                try:
                    dice_size = int(dice_size)
                    if dice_size < 2:
                        raise WrongDiceSize(dice_size)
                except ValueError:
                    # If not, give up and throw error
                    raise WrongCommandFormula(cmd)
                # Do the same to modifier, but cast it to float
                try:
                    modifier = float(modifier)
                    if modifier.is_integer():
                        modifier = int(modifier)
                    if modifier == 0 and operator == '/':
                        raise DivisionByZeroError
                except ValueError:
                    raise WrongCommandFormula(cmd)
        return n_rolls, dice_size, modifier, operator, threshold


def load(bot: lightbulb.Bot):
    bot.add_plugin(Roll())
